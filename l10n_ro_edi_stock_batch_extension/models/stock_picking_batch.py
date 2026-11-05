# Copyright 2026 NextERP Romania SRL
import base64

import markupsafe

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero

from odoo.addons.l10n_ro_edi_stock_extension.models.etransport_constants import (
    is_national,
    is_outgoing,
)
from odoo.addons.l10n_ro_edi_stock_extension.models.l10n_ro_edi_stock_document import (
    EXTRA_DOCUMENT_STATES,
    RECORD_STATE_ONDELETE,
)

# Context key set by the stock flows that legitimately take a transfer out of
# a batch (validation with backorders, cancellation of a transfer).
BATCH_DETACH_CTX = "l10n_ro_edi_stock_batch_detach"


class StockPickingBatch(models.Model):
    _name = "stock.picking.batch"
    _inherit = ["stock.picking.batch", "l10n.ro.edi.stock.integrity.mixin"]

    # The base ``l10n_ro_edi_stock_state`` field copies ``document.state`` into a
    # Selection limited to DOCUMENT_STATES. l10n_ro_edi_stock_extension adds extra
    # document states (deleted / confirmed / vehicle modified), so the batch
    # selection has to be widened too, otherwise the state compute raises
    # ``ValueError: Wrong value ... 'stock_vehicle_modified'``.
    l10n_ro_edi_stock_state = fields.Selection(
        selection_add=EXTRA_DOCUMENT_STATES,
        ondelete=RECORD_STATE_ONDELETE,
    )

    # Same configuration fields the extension adds on stock.picking, so the
    # batch eTransport notification benefits from the same facilities.
    l10n_ro_edi_stock_price_source = fields.Selection(
        selection=[
            ("auto", "Automatic (by operation)"),
            ("cost", "Cost price (standard_price)"),
            ("purchase", "Purchase order price"),
            ("sale", "Sale order price"),
            ("list", "Product list price"),
        ],
        default=lambda self: self._l10n_ro_edi_stock_default_price_source(),
        string="eTransport Price Source",
        help="Source for the VAT-excluded value sent to ANAF.\n"
        "Automatic: uses cost price on purchases and internal transfers; "
        "uses sale price on deliveries.",
    )

    l10n_ro_edi_stock_document_line_ids = fields.One2many(
        comodel_name="l10n.ro.edi.stock.document.line",
        inverse_name="batch_id",
        string="Transport Documents",
    )

    l10n_ro_edi_stock_previous_ids = fields.One2many(
        comodel_name="l10n.ro.edi.stock.previous.notification",
        inverse_name="batch_id",
        string="Previous Notifications",
    )

    l10n_ro_edi_stock_post_outage = fields.Boolean(
        string="Post-Outage Declaration",
        help="OUG 41/2022 art. 8 par. 1^3 - declaration allowed until the end "
        "of the next working day after the ANAF system is restored.",
    )

    ################################################################################
    # Integrity: a batch with a live UIT stays until ANAF is told otherwise
    ################################################################################

    def _l10n_ro_edi_stock_check_transfers_locked(self):
        if self.env.context.get(BATCH_DETACH_CTX):
            return
        for batch in self:
            document = batch._l10n_ro_edi_stock_live_uit_document()
            if document:
                raise UserError(
                    self.env._(
                        "The transfers of batch %(batch)s cannot be changed: its "
                        "eTransport notification (UIT %(uit)s) is registered at "
                        "ANAF for exactly these goods. Delete the notification "
                        "first.",
                        batch=batch.display_name,
                        uit=document.l10n_ro_edi_stock_uit,
                    )
                )

    def write(self, vals):
        if "picking_ids" in vals:
            self._l10n_ro_edi_stock_check_transfers_locked()
        locked = self.env["stock.picking"]._L10N_RO_EDI_STOCK_SENT_LOCKED_FIELDS
        if locked.intersection(vals):
            self._l10n_ro_edi_stock_check_not_sent()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_l10n_ro_edi_stock_live_uit(self):
        self._l10n_ro_edi_stock_check_no_live_uit(self.env._("deleted"))

    def action_cancel(self):
        self._l10n_ro_edi_stock_check_no_live_uit(self.env._("cancelled"))
        return super().action_cancel()

    def _is_picking_auto_mergeable(self, picking):
        # never slip a new transfer into goods already declared to ANAF
        if self._l10n_ro_edi_stock_live_uit_document():
            return False
        return super()._is_picking_auto_mergeable(picking)

    @api.depends("company_id", "state", "l10n_ro_edi_stock_state")
    def _compute_l10n_ro_edi_stock_enable_fetch(self):
        # EXTENDS: a deletion / confirmation / vehicle change waits for its
        # ANAF processing status the same way a notification does.
        res = super()._compute_l10n_ro_edi_stock_enable_fetch()
        for record in self:
            if (
                record.l10n_ro_edi_stock_enable
                and record.l10n_ro_edi_stock_state == "stock_action_sent"
            ):
                record.l10n_ro_edi_stock_enable_fetch = True
        return res

    def _l10n_ro_edi_stock_fetch_document_status(self):
        # EXTENDS: also fetch the status of pending DEL / CON / MVH uploads
        res = super()._l10n_ro_edi_stock_fetch_document_status()
        self._l10n_ro_edi_stock_fetch_pending_actions()
        return res

    @api.depends("l10n_ro_edi_stock_state")
    def _compute_l10n_ro_edi_stock_enable_amend(self):
        # EXTENDS l10n_ro_edi_stock_batch: a vehicle change keeps the
        # notification validated, so it can still be corrected.
        res = super()._compute_l10n_ro_edi_stock_enable_amend()
        for batch in self:
            if (
                batch.l10n_ro_edi_stock_enable
                and batch.l10n_ro_edi_stock_state == "stock_vehicle_modified"
                and batch._l10n_ro_edi_stock_get_last_document("stock_validated")
            ):
                batch.l10n_ro_edi_stock_enable_amend = True
        return res

    @api.model
    def _l10n_ro_edi_stock_default_price_source(self):
        return self.env.company.l10n_ro_edi_stock_default_price_source or "auto"

    ################################################################################
    # Send override - route the batch through the extension's picking logic
    ################################################################################

    def _l10n_ro_edi_stock_send_etransport_document(self, send_type: str):
        # EXTENDS l10n_ro_edi_stock_batch
        # Expose this batch via the context so the stock.picking override
        # (injected into _l10n_ro_edi_stock_validate_data /
        # _l10n_ro_edi_stock_get_template_data) treats it as the
        # ``_picking_record`` and applies all extension enrichments.
        self.ensure_one()
        # ``l10n_ro_edi_stock_xml_capture`` is a mutable side-channel: the
        # extension's _l10n_ro_edi_stock_get_template_data stores the final
        # template data into it so the amend correction XML can be re-rendered
        # below (see _l10n_ro_edi_stock_create_document_stock_sent).
        return super(
            StockPickingBatch,
            self.with_context(
                l10n_ro_edi_stock_batch_id=self.id,
                l10n_ro_edi_stock_event_send_type=send_type,
                l10n_ro_edi_stock_xml_capture={},
            ),
        )._l10n_ro_edi_stock_send_etransport_document(send_type=send_type)

    def _l10n_ro_edi_stock_create_document_stock_sent(self, values):
        # EXTENDS l10n_ro_edi_stock_batch:
        # 1) On amend, the base re-stores the original validated XML instead of
        #    the correction actually sent to ANAF (which contains <corectie>).
        #    Re-render the real correction from the captured template data so the
        #    stored document/attachment reflects what was transmitted.
        # 2) Tag the document with the ANAF event type (NOT / COR) so the
        #    eTransport Documents list can tell notifications and corrections apart.
        send_type = self.env.context.get("l10n_ro_edi_stock_event_send_type")
        capture = self.env.context.get("l10n_ro_edi_stock_xml_capture")
        if send_type == "amend" and capture and capture.get("data"):
            values = dict(values)
            values["raw_xml"] = markupsafe.Markup(
                "<?xml version='1.0' encoding='UTF-8'?>\n"
            ) + self.env["ir.qweb"]._render(
                "l10n_ro_edi_stock.l10n_ro_template_etransport",
                values={"data": capture["data"]},
            )
        document = super()._l10n_ro_edi_stock_create_document_stock_sent(values)
        if send_type and not document.l10n_ro_edi_stock_event_type:
            document.l10n_ro_edi_stock_event_type = (
                "COR" if send_type == "amend" else "NOT"
            )
        return document

    def _l10n_ro_edi_stock_report_unhandled_document_state(self, state):
        # EXTENDS l10n_ro_edi_stock_batch: persist a 'stock_sending_failed'
        # document for an unrecognised ANAF status (the base only logs it while
        # the fetch routine deletes the 'stock_sent' document), so the batch does
        # not silently lose its eTransport state.
        self.ensure_one()
        current = self.l10n_ro_edi_stock_document_ids.filtered(
            lambda d: d.state == "stock_sent"
        ).sorted()[:1]
        if current:
            failed_values = {
                "message": self.env._(
                    "Unhandled eTransport status returned by ANAF: %(state)s",
                    state=state,
                ),
                "l10n_ro_edi_stock_load_id": current.l10n_ro_edi_stock_load_id,
                "l10n_ro_edi_stock_uit": current.l10n_ro_edi_stock_uit,
            }
            if current.attachment:
                failed_values["raw_xml"] = base64.b64decode(current.attachment).decode()
            self._l10n_ro_edi_stock_create_document_stock_sending_failed(failed_values)
        return super()._l10n_ro_edi_stock_report_unhandled_document_state(state)

    ################################################################################
    # Duck-typing: the extension's template/validation code calls these helpers on
    # the ``_picking_record``. The stateless ones simply delegate to stock.picking;
    # the record-dependent ones (value, address) are implemented for the batch.
    ################################################################################

    def _l10n_ro_edi_stock_get_qty_and_uom(self, move):
        return self.env["stock.picking"]._l10n_ro_edi_stock_get_qty_and_uom(move)

    def _l10n_ro_edi_stock_compute_net_weight(self, move):
        return self.env["stock.picking"]._l10n_ro_edi_stock_compute_net_weight(move)

    def _l10n_ro_edi_stock_compute_gross_weight(self, move):
        return self.env["stock.picking"]._l10n_ro_edi_stock_compute_gross_weight(move)

    def _l10n_ro_edi_stock_get_codtarifar(self, product):
        return self.env["stock.picking"]._l10n_ro_edi_stock_get_codtarifar(product)

    @api.model
    def _l10n_ro_edi_stock_split_street(self, street):
        return self.env["stock.picking"]._l10n_ro_edi_stock_split_street(street)

    def _l10n_ro_edi_stock_compute_value(self, move, op_type):
        """Batch counterpart of the picking helper.

        Reuses the per-move extraction helpers of the move's own picking
        (correct state/currency/dates) but applies the batch-level price
        source preference and direction.
        """
        self.ensure_one()
        picking = move.picking_id
        company_currency = self.company_id.currency_id
        source = self.l10n_ro_edi_stock_price_source or "auto"
        pt_code = picking.picking_type_code or self.picking_type_id.code
        if source == "auto":
            if is_outgoing(op_type) or (is_national(op_type) and pt_code == "outgoing"):
                source = "sale"
            else:
                source = "cost"
        value = 0.0
        if source == "cost":
            value = picking._l10n_ro_edi_stock_value_from_cost(move)
            if float_is_zero(value, precision_digits=2):
                value = picking._l10n_ro_edi_stock_value_from_purchase(move)
        elif source == "purchase":
            value = picking._l10n_ro_edi_stock_value_from_purchase(move)
            if float_is_zero(value, precision_digits=2):
                value = picking._l10n_ro_edi_stock_value_from_cost(move)
        elif source == "sale":
            value = picking._l10n_ro_edi_stock_value_from_sale(move)
            if float_is_zero(value, precision_digits=2):
                value = move.product_id.list_price
        elif source == "list":
            value = move.product_id.list_price

        product_currency = move.product_id.currency_id or company_currency
        if value and product_currency != company_currency:
            value = product_currency._convert(
                value,
                company_currency,
                self.company_id,
                self.scheduled_date or fields.Date.context_today(self),
            )
        return value

    def _l10n_ro_edi_stock_resolve_address_partner(self, loc_kind, op_type):
        """Same logic as the picking helper, using the batch warehouse and the
        (common) partner of the pickings in the batch.
        """
        self.ensure_one()
        code = self.picking_type_id.code
        warehouse_partner = self.picking_type_id.warehouse_id.partner_id
        partner = self.picking_ids[:1].partner_id
        if code == "outgoing":
            return warehouse_partner if loc_kind == "start" else partner
        if code == "incoming":
            return warehouse_partner if loc_kind == "end" else partner
        return warehouse_partner if loc_kind == "start" else partner
