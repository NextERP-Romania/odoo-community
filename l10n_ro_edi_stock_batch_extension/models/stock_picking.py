# Copyright 2026 NextERP Romania SRL
from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.depends("batch_id.state", "batch_id.l10n_ro_edi_stock_state")
    def _compute_l10n_ro_edi_stock_enable(self):
        # EXTENDS l10n_ro_edi_stock_batch
        # The base batch module disables eTransport on *any* picking that sits
        # in a batch, so the notification can only ever go out on the batch
        # itself - which the base only lets you send once the batch has left
        # 'draft'. l10n_ro_edi_stock_extension exists precisely to notify ANAF
        # *before* the goods move, so a picking has to stay sendable while its
        # batch is still in progress.
        #
        # Re-enable it, but only while the batch itself carries no eTransport
        # document: as soon as the batch has been sent (or the batch is done)
        # the batch notification is the authoritative one and the picking must
        # not be able to file a second UIT for the same goods.
        res = super()._compute_l10n_ro_edi_stock_enable()
        for picking in self:
            if (
                not picking.l10n_ro_edi_stock_enable
                and picking.batch_id
                and picking.batch_id.state != "done"
                and not picking.batch_id.l10n_ro_edi_stock_state
                and picking.picking_type_code != "internal"
                and picking.company_id.account_fiscal_country_id.code == "RO"
            ):
                picking.l10n_ro_edi_stock_enable = True
        return res

    # The batch send flow (l10n_ro_edi_stock_batch) reuses these @api.model
    # entry points on stock.picking to validate / render the eTransport
    # document. The l10n_ro_edi_stock_extension overrides only enrich the
    # result when ``data["_picking_record"]`` is set (through the picking-only
    # context). Here we inject the batch as that record so the batch gets the
    # exact same stricter validation and template enrichment as a picking.

    @api.model
    def _l10n_ro_edi_stock_validate_data(self, data: dict):
        self._l10n_ro_edi_stock_inject_batch_record(data)
        return super()._l10n_ro_edi_stock_validate_data(data=data)

    @api.model
    def _l10n_ro_edi_stock_get_template_data(self, data: dict):
        self._l10n_ro_edi_stock_inject_batch_record(data)
        result = super()._l10n_ro_edi_stock_get_template_data(data=data)
        record = data.get("_picking_record")
        if record and record._name == "stock.picking.batch":
            # The base builder derives the 'PF' commercial partner code from
            # ``self.l10n_ro_edi_stock_operation_type`` which is empty when the
            # batch path calls this @api.model method on the model recordset.
            # Re-derive it here from the data dict.
            partner = data["partner_id"].commercial_partner_id
            partner_node = result["data"]["notificare"]["partenerComercial"]
            if (
                not partner_node.get("cod")
                and not partner.vat
                and data.get("l10n_ro_edi_stock_operation_type") == "30"
            ):
                partner_node["cod"] = "PF"
        return result

    @api.model
    def _l10n_ro_edi_stock_inject_batch_record(self, data):
        batch_id = self.env.context.get("l10n_ro_edi_stock_batch_id")
        if batch_id and not data.get("_picking_record"):
            data["_picking_record"] = self.env["stock.picking.batch"].browse(batch_id)
