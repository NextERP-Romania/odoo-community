# Copyright 2026 NextERP Romania SRL
import base64
import logging

import markupsafe

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models.etransport_api_extra import ETransportAPIExtra

_logger = logging.getLogger(__name__)


ACTION_TYPES = [
    ("delete", "Delete notification"),
    ("confirm", "Confirm transport"),
    ("modify_vehicle", "Modify vehicle"),
]


class L10nRoEdiStockActionWizard(models.TransientModel):
    _name = "l10n.ro.edi.stock.action.wizard"
    _description = "eTransport UIT action wizard (delete / confirm / modify vehicle)"

    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Transfer",
        required=True,
    )
    action_type = fields.Selection(
        selection=ACTION_TYPES,
        string="ANAF Action",
        required=True,
    )
    uit = fields.Char(string="Notification UIT", required=True, readonly=True)
    remarks = fields.Char(size=200)
    post_outage = fields.Boolean(string="Post-outage declaration")

    # For confirmation
    confirmation_type = fields.Selection(
        selection=[
            ("10", "Confirmed"),
            ("20", "Partially confirmed"),
            ("30", "Refused"),
        ],
    )

    # For vehicle modification
    new_vehicle_number = fields.Char(string="New vehicle number", size=20)
    trailer_1_number = fields.Char(string="Trailer 1 number", size=20)
    trailer_2_number = fields.Char(string="Trailer 2 number", size=20)
    modification_date = fields.Datetime(
        string="Vehicle modification date",
        default=fields.Datetime.now,
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        active_id = self.env.context.get("active_id")
        if active_id and self.env.context.get("active_model") == "stock.picking":
            picking = self.env["stock.picking"].browse(active_id)
            defaults["picking_id"] = picking.id
            defaults["uit"] = picking.l10n_ro_edi_stock_document_uit
            defaults["new_vehicle_number"] = picking.l10n_ro_edi_stock_vehicle_number
            defaults["trailer_1_number"] = picking.l10n_ro_edi_stock_trailer_1_number
            defaults["trailer_2_number"] = picking.l10n_ro_edi_stock_trailer_2_number
        return defaults

    def action_execute(self):
        self.ensure_one()
        if not self.uit:
            raise UserError(self.env._("The transfer has no validated UIT."))
        method = {
            "delete": self._send_delete,
            "confirm": self._send_confirm,
            "modify_vehicle": self._send_modify_vehicle,
        }[self.action_type]
        return method()

    def _render(self, template_xmlid, data):
        return markupsafe.Markup("<?xml version='1.0' encoding='UTF-8'?>\n") + self.env[
            "ir.qweb"
        ]._render(template_xmlid, values={"data": data})

    def _common_data(self):
        picking = self.picking_id
        company = picking.company_id
        return {
            "codDeclarant": (company.vat or "").upper().replace("RO", ""),
            "refDeclarant": (picking.name or "")[:50],
            "uit": self.uit,
            "remarks": (self.remarks or "")[:200] or None,
            "declPostAvarie": "D" if self.post_outage else None,
        }

    def _send_delete(self):
        data = self._common_data()
        raw_xml = self._render(
            "l10n_ro_edi_stock_extension.l10n_ro_template_etransport_delete",
            data,
        )
        return self._upload_and_log(
            raw_xml, event_type="DEL", new_state="stock_deleted"
        )

    def _send_confirm(self):
        if not self.confirmation_type:
            raise UserError(self.env._("Confirmation type is required."))
        data = self._common_data()
        data["tipConfirmare"] = self.confirmation_type
        raw_xml = self._render(
            "l10n_ro_edi_stock_extension.l10n_ro_template_etransport_confirm",
            data,
        )
        return self._upload_and_log(
            raw_xml,
            event_type="CON",
            new_state="stock_confirmed",
            extras={"l10n_ro_edi_stock_confirm_type": self.confirmation_type},
        )

    def _send_modify_vehicle(self):
        if not self.new_vehicle_number:
            raise UserError(self.env._("Vehicle number is required."))
        if not self.modification_date:
            raise UserError(self.env._("Modification date is required."))
        data = self._common_data()
        data.update(
            {
                "nrVehicul": self.new_vehicle_number.upper(),
                "nrRemorca1": self.trailer_1_number.upper()
                if self.trailer_1_number
                else None,
                "nrRemorca2": self.trailer_2_number.upper()
                if self.trailer_2_number
                else None,
                "dataModificare": self.modification_date.strftime("%Y-%m-%dT%H:%M:%S"),
            }
        )
        raw_xml = self._render(
            "l10n_ro_edi_stock_extension.l10n_ro_template_etransport_modify_vehicle",
            data,
        )
        result = self._upload_and_log(
            raw_xml,
            event_type="MVH",
            new_state="stock_vehicle_modified",
            extras={
                "l10n_ro_edi_stock_modified_vehicle": self.new_vehicle_number,
                "l10n_ro_edi_stock_modification_date": self.modification_date,
            },
        )
        # Update the fields on the picking for history tracking
        if isinstance(result, dict) and not result.get("error"):
            self.picking_id.write(
                {
                    "l10n_ro_edi_stock_vehicle_number": self.new_vehicle_number,
                    "l10n_ro_edi_stock_trailer_1_number": self.trailer_1_number
                    or False,
                    "l10n_ro_edi_stock_trailer_2_number": self.trailer_2_number
                    or False,
                }
            )
        return result

    def _upload_and_log(self, raw_xml, event_type, new_state, extras=None):
        result = ETransportAPIExtra().upload_data(
            company_id=self.picking_id.company_id,
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
            "picking_id": self.picking_id.id,
            "state": new_state,
            "l10n_ro_edi_stock_load_id": content["index_incarcare"],
            "l10n_ro_edi_stock_uit": self.uit,
            "l10n_ro_edi_stock_event_type": event_type,
            "attachment": base64.b64encode(raw_xml.encode("utf-8")),
        }
        if extras:
            values.update(extras)
        self.env["l10n_ro_edi.document"].create(values)
        self.picking_id._message_log(
            body=self.env._(
                "eTransport %(action)s sent successfully "
                "(UIT: %(uit)s, load: %(load)s).",
                action=event_type,
                uit=self.uit,
                load=content["index_incarcare"],
            ),
        )
        return {"type": "ir.actions.act_window_close"}
