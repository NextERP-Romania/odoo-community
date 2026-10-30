# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.exceptions import UserError


class MessageSPV(models.Model):
    _inherit = "l10n.ro.message.spv"

    l10n_ro_is_autoinvoice = fields.Boolean(
        string="Self-Invoice",
        readonly=True,
        help="Invoice issued by the customer in our name (autofactura).",
    )

    def get_xml_fom_zip(self):
        res = super().get_xml_fom_zip()
        move_obj = self.env["account.move"]
        received_types = ("in_invoice", "in_receipt")
        for message in self.filtered(
            lambda m: not m.invoice_id
            and not m.l10n_ro_is_autoinvoice
            and m.message_type in (*received_types, "out_invoice", "out_receipt")
        ):
            _file_name, xml_bytes = message._get_xml_bytes()
            customer_vat = move_obj._l10n_ro_edi_autoinvoice_customer_vat(
                message.company_id,
                xml_bytes,
                received=message.message_type in received_types,
            )
            if not customer_vat:
                continue
            # The customer issued it, so it is a sale and the partner is the
            # customer, not the company itself (the cif_emitent of a received
            # self-invoice).
            message.write(
                {
                    "l10n_ro_is_autoinvoice": True,
                    "message_type": "out_receipt"
                    if message.message_type in ("in_receipt", "out_receipt")
                    else "out_invoice",
                    "cif": customer_vat,
                    "partner_id": message.company_id._l10n_ro_get_partner_from_cif(
                        customer_vat
                    ).id,
                }
            )
        return res

    def create_invoice(self):
        autoinvoices = self.filtered(
            lambda m: m.l10n_ro_is_autoinvoice and not m.invoice_id
        )
        for message in autoinvoices:
            message.get_invoice_from_move()
            if message.invoice_id:
                continue
            file_name, xml_bytes = message._get_xml_bytes()
            if not xml_bytes:
                message.write(
                    {"state": "error", "error": "No XML found in the downloaded ZIP."}
                )
                continue
            try:
                move = self.env["account.move"]._l10n_ro_edi_create_autoinvoice(
                    message.company_id,
                    xml_bytes,
                    file_name,
                    message.request_id,
                    document_vals={"key_download": message.name},
                )
            except UserError as e:
                message.write({"state": "error", "error": str(e)})
                continue
            move.write(
                {
                    "l10n_ro_edi_download": message.name,
                    "l10n_ro_edi_transaction": message.request_id,
                }
            )
            message.write({"invoice_id": move.id})
            message.get_data_from_invoice()
        return super(MessageSPV, self - autoinvoices).create_invoice()
