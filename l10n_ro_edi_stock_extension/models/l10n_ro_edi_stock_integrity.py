# Copyright 2026 NextERP Romania SRL
import requests

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_ro_edi_stock.models.etransport_api import ETransportAPI

from .l10n_ro_edi_stock_document import (
    ACTION_FINAL_STATES,
    PENDING_ACTION_STATE,
    UIT_ACTION_STATES,
    l10n_ro_edi_stock_effective_document,
    l10n_ro_edi_stock_live_uit_document,
)


class L10nRoEdiStockIntegrityMixin(models.AbstractModel):
    """Guards shared by the records an eTransport notification is filed on
    (transfers, and batches in l10n_ro_edi_stock_batch_extension). They carry
    ``l10n_ro_edi_stock_document_ids`` and ``l10n_ro_edi_stock_state``."""

    _name = "l10n.ro.edi.stock.integrity.mixin"
    _description = "eTransport notification integrity"

    # Whether ANAF would accept a deletion / confirmation / vehicle change now:
    # the notification is validated (possibly with a changed vehicle), even if
    # a later attempt failed, and no other action is waiting for ANAF.
    l10n_ro_edi_stock_enable_uit_action = fields.Boolean(
        string="eTransport Action Allowed",
        compute="_compute_l10n_ro_edi_stock_enable_uit_action",
    )

    @api.depends("l10n_ro_edi_stock_document_ids.state")
    def _compute_l10n_ro_edi_stock_enable_uit_action(self):
        for record in self:
            document = l10n_ro_edi_stock_effective_document(
                record.l10n_ro_edi_stock_document_ids
            )
            record.l10n_ro_edi_stock_enable_uit_action = (
                document.state in UIT_ACTION_STATES
            )

    def _l10n_ro_edi_stock_live_uit_document(self):
        self.ensure_one()
        return l10n_ro_edi_stock_live_uit_document(self.l10n_ro_edi_stock_document_ids)

    def _l10n_ro_edi_stock_check_no_live_uit(self, action):
        for record in self:
            document = record._l10n_ro_edi_stock_live_uit_document()
            if document:
                raise UserError(
                    self.env._(
                        "%(record)s cannot be %(action)s: its eTransport "
                        "notification (UIT %(uit)s) is registered at ANAF. "
                        "Delete the notification first.",
                        record=record.display_name,
                        action=action,
                        uit=document.l10n_ro_edi_stock_uit,
                    )
                )

    def _l10n_ro_edi_stock_check_not_sent(self):
        if self.env.context.get("l10n_ro_edi_stock_skip_sent_lock"):
            return
        for record in self:
            if record.l10n_ro_edi_stock_state == "stock_sent":
                raise UserError(
                    self.env._(
                        "The eTransport data of %(record)s cannot be changed "
                        "while ANAF is processing its notification. Fetch the "
                        "status first.",
                        record=record.display_name,
                    )
                )

    ################################################################################
    # Processing status of a deletion / confirmation / vehicle change
    ################################################################################

    def _l10n_ro_edi_stock_fetch_pending_actions(self):
        """Ask ANAF how it processed the DEL / CON / MVH uploads waiting in
        ``stock_action_sent``, the same way the base module fetches a sent
        notification: accepted -> the action's state; refused -> error, which
        leaves the UIT where it was before the action; still in progress or
        ANAF unreachable -> the document keeps waiting."""
        session = requests.Session()
        for record in self:
            pending = record.l10n_ro_edi_stock_document_ids.filtered(
                lambda d: d.state == PENDING_ACTION_STATE
            ).sorted()
            if not pending:
                continue
            if not record.company_id.l10n_ro_edi_access_token:
                record._message_log(
                    body=self.env._(
                        "Romanian access token not found. Please generate or "
                        "fill it in the settings."
                    )
                )
                continue
            for document in pending:
                result = ETransportAPI().get_status(
                    company_id=record.company_id,
                    document_load_id=document.l10n_ro_edi_stock_load_id,
                    session=session,
                )
                if "error" in result:
                    record._message_log(
                        body=self.env._(
                            "eTransport %(action)s status could not be fetched "
                            "(load %(load)s): %(err)s",
                            action=document.l10n_ro_edi_stock_event_type,
                            load=document.l10n_ro_edi_stock_load_id,
                            err=result["error"],
                        )
                    )
                    continue
                content = result.get("content") or {}
                state = content.get("stare")
                if state == "in prelucrare":
                    continue
                if state == "ok":
                    record._l10n_ro_edi_stock_apply_accepted_action(document)
                    continue
                if state == "XML cu erori nepreluat de sistem":
                    message = self.env._("XML contains errors.")
                else:
                    message = self.env._(
                        "ANAF refused the %(action)s (status: %(state)s).",
                        action=document.l10n_ro_edi_stock_event_type,
                        state=state,
                    )
                details = [
                    error.get("errorMessage")
                    for error in content.get("Errors") or []
                    if isinstance(error, dict) and error.get("errorMessage")
                ]
                if details:
                    message = "\n".join([message, *details])
                record._l10n_ro_edi_stock_write_document(
                    document, {"state": "stock_sending_failed", "message": message}
                )
                record._message_log(
                    body=self.env._(
                        "eTransport %(action)s refused by ANAF (UIT: %(uit)s): "
                        "%(message)s",
                        action=document.l10n_ro_edi_stock_event_type,
                        uit=document.l10n_ro_edi_stock_uit,
                        message=message,
                    )
                )

    def _l10n_ro_edi_stock_write_document(self, document, vals):
        """Move a document to its next state in place, keeping the XML that
        was sent. The state copied on the record only depends on the document
        list, so it is recomputed explicitly."""
        self.ensure_one()
        document.write(vals)
        for fname in ("l10n_ro_edi_stock_state", "l10n_ro_edi_stock_document_uit"):
            field = self._fields[fname]
            if field.store:
                self.env.add_to_compute(field, self)
            else:
                self.invalidate_recordset([fname])

    def _l10n_ro_edi_stock_apply_accepted_action(self, document):
        self.ensure_one()
        self._l10n_ro_edi_stock_write_document(
            document,
            {"state": ACTION_FINAL_STATES[document.l10n_ro_edi_stock_event_type]},
        )
        if document.l10n_ro_edi_stock_event_type == "MVH":
            # only now is the new vehicle the one ANAF knows
            self.write(
                {
                    "l10n_ro_edi_stock_vehicle_number": (
                        document.l10n_ro_edi_stock_modified_vehicle
                    ),
                    "l10n_ro_edi_stock_trailer_1_number": (
                        document.l10n_ro_edi_stock_modified_trailer_1 or False
                    ),
                    "l10n_ro_edi_stock_trailer_2_number": (
                        document.l10n_ro_edi_stock_modified_trailer_2 or False
                    ),
                }
            )
        self._message_log(
            body=self.env._(
                "eTransport %(action)s accepted by ANAF (UIT: %(uit)s).",
                action=document.l10n_ro_edi_stock_event_type,
                uit=document.l10n_ro_edi_stock_uit,
            )
        )

    @api.model
    def _l10n_ro_edi_stock_cron_fetch_status(self):
        """Fetch the ANAF status of every notification and action still
        waiting for it."""
        records = self.search(
            [("l10n_ro_edi_stock_state", "in", ("stock_sent", PENDING_ACTION_STATE))]
        )
        records._l10n_ro_edi_stock_fetch_document_status()
