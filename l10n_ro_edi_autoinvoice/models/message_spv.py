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

    def get_invoice_from_move(self):
        """
        ANAF lists a self-invoice without cif_emitent, so until its XML is
        read (get_xml_fom_zip) the message keeps the CIF of the company and
        the company as partner. The standard matching links it to the
        self-invoice "Synchronize with ANAF" already took in, by its SPV
        index, but leaves it as a received message of the company. Before
        that matching, mark the messages of an invoice of a customer
        self-invoicing journal (autoinv1), found by its SPV index or download
        id, and give them the customer: from the XML, downloading the ZIP if
        it is missing, or else from the invoice. A self-invoice left in draft
        in another sale journal is still linked by the standard matching, but
        its message is not marked.
        """
        received_types = ("in_invoice", "in_receipt")
        messages = self.filtered(
            lambda m: not m.invoice_id
            and not m.l10n_ro_is_autoinvoice
            and m.message_type in (*received_types, "out_invoice", "out_receipt")
        )
        if messages:
            autoinvoices = self.env["account.move"].search(
                [
                    ("company_id", "in", messages.company_id.ids),
                    ("journal_id.l10n_ro_sequence_type", "=", "autoinv1"),
                    ("state", "!=", "cancel"),
                    "|",
                    ("l10n_ro_edi_index", "in", messages.mapped("request_id")),
                    ("l10n_ro_edi_download", "in", messages.mapped("name")),
                ]
            )
            for message in messages:
                invoice = autoinvoices.filtered(
                    lambda i, m=message: i.company_id == m.company_id
                    and (
                        i.l10n_ro_edi_index == m.request_id
                        or i.l10n_ro_edi_download == m.name
                    )
                )[:1]
                if not invoice:
                    continue
                if not message.attachment_id:
                    # Get the ZIP now, so the message gets its data (ref,
                    # amount, ZIP) without a separate Download; reading its
                    # XML (get_xml_fom_zip) also marks it as a self-invoice.
                    message.download_from_spv()
                if message.l10n_ro_is_autoinvoice:
                    continue
                # No XML (the download failed, the error is on the message):
                # the customer comes from the invoice.
                customer = invoice.commercial_partner_id
                message.write(
                    {
                        "l10n_ro_is_autoinvoice": True,
                        "message_type": "out_receipt"
                        if message.message_type in ("in_receipt", "out_receipt")
                        else "out_invoice",
                        "cif": customer.l10n_ro_vat_number,
                        "partner_id": customer.id,
                    }
                )
        return super().get_invoice_from_move()

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
