# Copyright 2026 NextERP Romania SRL
import base64

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_ro_edi_stock_extension.models.etransport_api_extra import (
    ETransportAPIExtra,
)


class L10nRoEdiStockActionWizard(models.TransientModel):
    _inherit = "l10n.ro.edi.stock.action.wizard"

    batch_id = fields.Many2one(
        comodel_name="stock.picking.batch",
        string="Batch Transfer",
    )
    # The picking is no longer mandatory: the wizard can act on a batch instead.
    picking_id = fields.Many2one(required=False)

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id")
        if active_id and self.env.context.get("active_model") == "stock.picking.batch":
            batch = self.env["stock.picking.batch"].browse(active_id)
            defaults["batch_id"] = batch.id
            defaults["uit"] = batch.l10n_ro_edi_stock_document_uit
            defaults["new_vehicle_number"] = batch.l10n_ro_edi_stock_vehicle_number
            defaults["trailer_1_number"] = batch.l10n_ro_edi_stock_trailer_1_number
            defaults["trailer_2_number"] = batch.l10n_ro_edi_stock_trailer_2_number
        return defaults

    def _common_data(self):
        if not self.batch_id:
            return super()._common_data()
        batch = self.batch_id
        company = batch.company_id
        return {
            "codDeclarant": (company.vat or "").upper().replace("RO", ""),
            "refDeclarant": (batch.name or "")[:50],
            "uit": self.uit,
            "remarks": (self.remarks or "")[:200] or None,
            "declPostAvarie": "D" if self.post_outage else None,
        }

    def _upload_and_log(self, raw_xml, event_type, new_state, extras=None):
        if not self.batch_id:
            return super()._upload_and_log(
                raw_xml, event_type, new_state, extras=extras
            )
        result = ETransportAPIExtra().upload_data(
            company_id=self.batch_id.company_id,
            data=raw_xml,
        )
        if "error" in result:
            raise UserError(
                self.env._(
                    "ANAF error on %(action)s: %(err)s",
                    action=event_type,
                    err=result["error"],
                )
            )
        content = result["content"]
        values = {
            "batch_id": self.batch_id.id,
            "state": new_state,
            "l10n_ro_edi_stock_load_id": content["index_incarcare"],
            "l10n_ro_edi_stock_uit": self.uit,
            "l10n_ro_edi_stock_event_type": event_type,
            "attachment": base64.b64encode(raw_xml.encode("utf-8")),
        }
        if extras:
            values.update(extras)
        self.env["l10n_ro_edi.document"].create(values)
        self.batch_id._message_log(
            body=self.env._(
                "eTransport %(action)s sent successfully "
                "(UIT: %(uit)s, load: %(load)s).",
                action=event_type,
                uit=self.uit,
                load=content["index_incarcare"],
            ),
        )
        return {"type": "ir.actions.act_window_close"}

    def _send_modify_vehicle(self):
        result = super()._send_modify_vehicle()
        # super() writes the new vehicle numbers back on picking_id (empty for a
        # batch, so a no-op); mirror that write on the batch record.
        if self.batch_id and isinstance(result, dict) and not result.get("error"):
            self.batch_id.write(
                {
                    "l10n_ro_edi_stock_vehicle_number": self.new_vehicle_number,
                    "l10n_ro_edi_stock_trailer_1_number": self.trailer_1_number
                    or False,
                    "l10n_ro_edi_stock_trailer_2_number": self.trailer_2_number
                    or False,
                }
            )
        return result
