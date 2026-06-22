# Copyright 2026 NextERP Romania SRL
from odoo import fields, models
from odoo.exceptions import UserError

from ..models.etransport_api_extra import ETransportAPIExtra


class L10nRoEdiStockTransporterInfoWizard(models.TransientModel):
    _name = "l10n.ro.edi.stock.transporter.info.wizard"
    _description = "eTransport transporter info wizard"

    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    operator_vat = fields.Char(string="Transport operator VAT", required=True)
    declarant_vat = fields.Char(string="Initial declarant VAT")
    uit = fields.Char(string="Specific UIT")
    declarant_ref = fields.Char(string="Declarant reference")
    line_ids = fields.One2many(
        comodel_name="l10n.ro.edi.stock.transporter.info.line",
        inverse_name="wizard_id",
    )

    def action_fetch(self):
        self.ensure_one()
        if not self.operator_vat:
            raise UserError(self.env._("Transport operator VAT is required."))
        result = ETransportAPIExtra().get_transporter_info(
            company_id=self.company_id,
            cui_op=self.operator_vat.replace("RO", ""),
            cui_decl=self.declarant_vat.replace("RO", "")
            if self.declarant_vat
            else None,
            uit=self.uit,
            ref_decl=self.declarant_ref,
        )
        if "error" in result:
            raise UserError(self.env._("ANAF error: %(err)s", err=result["error"]))

        self.line_ids = [(5, 0, 0)]
        rows = (
            result["content"]
            if isinstance(result["content"], list)
            else result["content"].get("inregistrari", [])
        )
        line_vals = []
        for row in rows:
            line_vals.append(
                (
                    0,
                    0,
                    {
                        "uit": row.get("uit"),
                        "declarant_vat": row.get("cod_decl"),
                        "declarant_name": row.get("den_decl"),
                        "declarant_ref": row.get("ref_decl"),
                        "transport_date": row.get("data_transp"),
                        "uit_expiry_date": row.get("data_exp_uit"),
                        "transporter_vat": row.get("tr_cod"),
                        "transporter_name": row.get("tr_den"),
                        "vehicle_number": row.get("nr_veh"),
                        "trailer_1_number": row.get("nr_rem1"),
                        "trailer_2_number": row.get("nr_rem2"),
                        "start_location": self._format_loc(row.get("loc_start")),
                        "end_location": self._format_loc(row.get("loc_final")),
                    },
                )
            )
        self.line_ids = line_vals
        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n.ro.edi.stock.transporter.info.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @staticmethod
    def _format_loc(loc):
        if not loc:
            return ""
        return loc.get("adresa_completa") or " ".join(
            filter(
                None,
                [
                    loc.get("strada"),
                    loc.get("numar"),
                    loc.get("localitate"),
                    loc.get("judet"),
                ],
            )
        )


class L10nRoEdiStockTransporterInfoLine(models.TransientModel):
    _name = "l10n.ro.edi.stock.transporter.info.line"
    _description = "eTransport transporter info line"

    wizard_id = fields.Many2one(
        comodel_name="l10n.ro.edi.stock.transporter.info.wizard", ondelete="cascade"
    )
    uit = fields.Char(string="UIT")
    declarant_vat = fields.Char(string="Declarant VAT")
    declarant_name = fields.Char()
    declarant_ref = fields.Char(string="Declarant Reference")
    transport_date = fields.Char()
    uit_expiry_date = fields.Char(string="UIT Expiry Date")
    transporter_vat = fields.Char(string="Transporter VAT")
    transporter_name = fields.Char()
    vehicle_number = fields.Char()
    trailer_1_number = fields.Char()
    trailer_2_number = fields.Char()
    start_location = fields.Char()
    end_location = fields.Char()
