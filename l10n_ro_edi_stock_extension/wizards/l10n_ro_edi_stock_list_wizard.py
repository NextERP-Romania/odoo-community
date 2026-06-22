# Copyright 2026 NextERP Romania SRL
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

from ..models.etransport_api_extra import ETransportAPIExtra

_logger = logging.getLogger(__name__)


class L10nRoEdiStockListWizard(models.TransientModel):
    _name = "l10n.ro.edi.stock.list.wizard"
    _description = "eTransport notifications list sync wizard"

    days = fields.Integer(string="Number of days (1-60)", default=14, required=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        default=lambda self: self.env.company,
        required=True,
    )
    line_ids = fields.One2many(
        comodel_name="l10n.ro.edi.stock.list.line",
        inverse_name="wizard_id",
        string="Returned notifications",
    )

    def action_fetch(self):
        self.ensure_one()
        if self.days < 1 or self.days > 60:
            raise UserError(self.env._("Number of days must be between 1 and 60."))
        result = ETransportAPIExtra().get_list(
            company_id=self.company_id,
            days=self.days,
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
                        "wizard_id": self.id,
                        "notification_type": row.get("tip"),
                        "status": row.get("stare"),
                        "uit": row.get("uit"),
                        "declarant_vat": row.get("cod_decl"),
                        "declarant_ref": row.get("ref_decl"),
                        "load_id": row.get("id_incarcare"),
                        "operation_type": str(row.get("tip_op") or ""),
                        "transport_date": row.get("data_transp"),
                        "partner_vat": row.get("pc_cod"),
                        "partner_name": row.get("pc_den"),
                        "transporter_vat": row.get("tr_cod"),
                        "transporter_name": row.get("tr_den"),
                        "vehicle_number": row.get("nr_veh"),
                        "messages": self._format_messages(row.get("mesaje")),
                    },
                )
            )
        self.line_ids = line_vals

        # Auto-reconcile with pickings based on UIT
        self._reconcile_with_pickings()

        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n.ro.edi.stock.list.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    @api.model
    def _format_messages(self, mesaje):
        if not mesaje:
            return ""
        return "\n".join(
            f"[{m.get('tip')}] {m.get('mesaj')}"
            for m in (mesaje if isinstance(mesaje, list) else [])
        )

    def _reconcile_with_pickings(self):
        """Log in chatter the pickings whose UIT was found in the ANAF list.

        Informative only - does not change states (the user decides the
        follow-up actions).
        """
        uits = {ln.uit for ln in self.line_ids if ln.uit}
        if not uits:
            return
        pickings = self.env["stock.picking"].search(
            [
                ("l10n_ro_edi_stock_document_uit", "in", list(uits)),
            ]
        )
        for pk in pickings:
            line = self.line_ids.filtered(
                lambda ln, u=pk.l10n_ro_edi_stock_document_uit: ln.uit == u
            )[:1]
            if line and line.status == "ERR":
                pk._message_log(
                    body=self.env._(
                        "Notification with errors found via ANAF LIST: %(m)s",
                        m=line.messages,
                    )
                )


class L10nRoEdiStockListLine(models.TransientModel):
    _name = "l10n.ro.edi.stock.list.line"
    _description = "eTransport notifications list line"

    wizard_id = fields.Many2one(
        comodel_name="l10n.ro.edi.stock.list.wizard", ondelete="cascade"
    )
    notification_type = fields.Char()
    status = fields.Char()
    uit = fields.Char(string="UIT")
    declarant_vat = fields.Char(string="Declarant VAT")
    declarant_ref = fields.Char(string="Declarant Reference")
    load_id = fields.Char(string="Load ID")
    operation_type = fields.Char()
    transport_date = fields.Char()
    partner_vat = fields.Char(string="Partner VAT")
    partner_name = fields.Char()
    transporter_vat = fields.Char(string="Transporter VAT")
    transporter_name = fields.Char()
    vehicle_number = fields.Char()
    messages = fields.Text()
