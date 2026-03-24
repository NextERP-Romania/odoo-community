# Copyright (C) 2022 Dorin Hongu <dhongu(@)gmail(.)com
# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from base64 import b64decode, b64encode

import requests

from odoo import _, models
from odoo.exceptions import UserError


class AccountEdiXmlCIUSRO(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_ro"

    def _get_tax_category_list(self, customer, supplier, taxes):
        vals_list = super()._get_tax_category_list(customer, supplier, taxes)
        for vals in vals_list:
            word_to_check = "Invers"
            if any(
                word_to_check.lower() in word.lower() for word in taxes.mapped("name")
            ):
                vals["id"] = "AE"
                vals["tax_category_code"] = "AE"
                vals["tax_exemption_reason_code"] = "VATEX-EU-AE"
                vals["tax_exemption_reason"] = ""
            if vals["percent"] == 0 and vals["tax_category_code"] != "AE":
                vals["id"] = "Z"
                vals["tax_category_code"] = "Z"
                vals["tax_exemption_reason"] = ""

        return vals_list

    def _get_invoice_tax_totals_vals_list(self, invoice, taxes_vals):
        vals_list = super()._get_invoice_tax_totals_vals_list(invoice, taxes_vals)
        if (
            invoice.move_type in ["out_refund", "in_refund"]
            and invoice.company_id.l10n_ro_credit_note_einvoice
        ):
            vals_list[0].update({"tax_amount": -1 * taxes_vals["tax_amount_currency"]})
            for vals in taxes_vals["tax_details"].values():
                vals["taxable_amount"] = -1 * vals["base_amount_currency"]
                vals["tax_amount"] = -1 * vals["tax_amount_currency"]
        return vals_list

    def _get_invoice_line_vals(self, line, line_id, taxes_vals):
        res = super()._get_invoice_line_vals(line, line_id, taxes_vals)
        if (
            line.move_id.move_type in ["out_refund", "in_refund"]
            and line.company_id.l10n_ro_credit_note_einvoice
        ):
            if res.get("invoiced_quantity", 0):
                res["invoiced_quantity"] = (-1) * res["invoiced_quantity"]
            if res.get("line_extension_amount", 0):
                res["line_extension_amount"] = (-1) * res["line_extension_amount"]
            if res.get("tax_total_vals"):
                for tax in res["tax_total_vals"]:
                    if tax["tax_amount"]:
                        tax["tax_amount"] = (-1) * tax["tax_amount"]
                    if tax["taxable_amount"]:
                        tax["taxable_amount"] = (-1) * tax["taxable_amount"]
        return res

    def _get_invoice_line_item_vals(self, line, taxes_vals):
        vals = super()._get_invoice_line_item_vals(line, taxes_vals)
        vals["description"] = vals["description"][:200]
        vals["name"] = vals["name"][:100]
        if vals["classified_tax_category_vals"]:
            if vals["classified_tax_category_vals"][0]["tax_category_code"] == "AE":
                vals["classified_tax_category_vals"][0]["tax_exemption_reason_code"] = (
                    ""
                )
                vals["classified_tax_category_vals"][0]["tax_exemption_reason"] = ""
        return vals

    def _get_invoice_line_price_vals(self, line):
        vals = super()._get_invoice_line_price_vals(line)
        vals["base_quantity"] = 1.0
        return vals

    def _export_invoice_vals(self, invoice):
        vals_list = super()._export_invoice_vals(invoice)
        if "order_reference" in vals_list["vals"]:
            vals_list["vals"]["order_reference"] = vals_list["vals"]["order_reference"][
                :30
            ]
        if "sales_order_id" in vals_list["vals"]:
            vals_list["vals"]["sales_order_id"] = vals_list["vals"]["sales_order_id"][
                :200
            ]
        if invoice.currency_id.name != "RON":
            vals_list["vals"]["tax_currency_code"] = invoice.currency_id.name
        if (
            invoice.move_type in ["out_refund", "in_refund"]
            and invoice.company_id.l10n_ro_credit_note_einvoice
        ):
            if vals_list["vals"].get("legal_monetary_total_vals"):
                vals_list["vals"]["legal_monetary_total_vals"][
                    "tax_exclusive_amount"
                ] = (-1) * vals_list["vals"]["legal_monetary_total_vals"][
                    "tax_exclusive_amount"
                ]
                vals_list["vals"]["legal_monetary_total_vals"][
                    "tax_inclusive_amount"
                ] = (-1) * vals_list["vals"]["legal_monetary_total_vals"][
                    "tax_inclusive_amount"
                ]
                vals_list["vals"]["legal_monetary_total_vals"]["prepaid_amount"] = (
                    -1
                ) * vals_list["vals"]["legal_monetary_total_vals"]["prepaid_amount"]
                vals_list["vals"]["legal_monetary_total_vals"]["payable_amount"] = (
                    -1
                ) * vals_list["vals"]["legal_monetary_total_vals"]["payable_amount"]
        if invoice.is_l10n_ro_autoinvoice():
            customer = invoice.company_id.partner_id.commercial_partner_id
            supplier = invoice.partner_id
            vals_list.update({"customer": customer, "supplier": supplier})
            customer_vals = vals_list["vals"]["accounting_customer_party_vals"]
            vals_list["vals"].update(
                {
                    "accounting_customer_party_vals": vals_list["vals"][
                        "accounting_supplier_party_vals"
                    ],
                    "accounting_supplier_party_vals": customer_vals,
                }
            )
        result_list = []
        if vals_list["vals"].get("note_vals"):
            if len(vals_list["vals"]["note_vals"][0]) > 100:
                split_strings = self.split_string(vals_list["vals"]["note_vals"][0])
                for _index, split_str in enumerate(split_strings):
                    result_list.append(split_str)
        if result_list:
            vals_list["vals"]["note_vals"] = result_list
        return vals_list

    def _get_invoice_payment_means_vals_list(self, invoice):
        res = super()._get_invoice_payment_means_vals_list(invoice)
        if not invoice.partner_bank_id:
            for vals in res:
                vals.update(
                    {
                        "payment_means_code": "1",
                        "payment_means_code_attrs": {"name": "Not Defined"},
                    }
                )
        return res

    def _import_fill_invoice_line_form(self, tree, invoice_line, qty_factor):
        vat_on_payment = False
        if invoice_line.partner_id.l10n_ro_vat_on_payment:
            invoice_line.move_id.fiscal_position_id = (
                invoice_line.partner_id.property_account_position_id
            )
            vat_on_payment = True
        res = super()._import_fill_invoice_line_form(tree, invoice_line, qty_factor)
        if vat_on_payment:
            new_tax = invoice_line.move_id.fiscal_position_id.map_tax(
                invoice_line.tax_ids
            )
            invoice_line.tax_ids = [(5,)]
            invoice_line.tax_ids = [(4, new_tax.id)]

        tax_nodes = tree.findall(".//{*}Item/{*}ClassifiedTaxCategory/{*}ID")
        if len(tax_nodes) == 1:
            if tax_nodes[0].text in ["O", "E", "Z"]:
                # Acest TVA nu generaza inregistrari contabile,
                # deci putem lua orice primul tva pe cota 0
                # filtrat dupa companie si tip jurnal.
                journal = invoice_line.move_id.journal_id
                tax = self.env["account.tax"].search(
                    [
                        ("amount", "=", "0"),
                        ("type_tax_use", "=", journal.type),
                        ("amount_type", "=", "percent"),
                        ("company_id", "=", invoice_line.company_id.id),
                    ],
                    limit=1,
                )
                if tax and not invoice_line.tax_ids:
                    invoice_line.tax_ids = [(5,)]  # Șterge toate valorile existente
                    invoice_line.tax_ids = [(4, tax.id)]  # Adaugă noua taxă
        return res

    def _import_fill_invoice_line_taxes(
        self, tax_nodes, invoice_line, inv_line_vals, logs
    ):
        if not invoice_line.account_id:
            invoice_line.account_id = invoice_line.move_id.journal_id.default_account_id
        if not inv_line_vals.get("account_id"):
            inv_line_vals["account_id"] = (
                invoice_line.move_id.journal_id.default_account_id.id
            )
        return super()._import_fill_invoice_line_taxes(
            tax_nodes, invoice_line, inv_line_vals, logs
        )

    def _get_document_type_code_vals(self, invoice, invoice_data):
        # EXTENDS 'account_edi_ubl_cii
        vals = super()._get_document_type_code_vals(invoice, invoice_data)
        # [UBL-SR-43] DocumentTypeCode should only show up on a CreditNote XML with the value '50'
        if invoice.move_type == "in_refund" and invoice.is_l10n_ro_autoinvoice():
            vals["value"] = "50"
        return vals

    def _import_partner(
        self,
        company_id,
        name,
        phone,
        email,
        vat,
        country_code=False,
        peppol_eas=False,
        peppol_endpoint=False,
        street=False,
        street2=False,
        city=False,
        zip_code=False,
    ):
        partner, logs = super()._import_partner(
            company_id,
            name,
            phone,
            email,
            vat,
            country_code,
            peppol_eas,
            peppol_endpoint,
            street,
            street2,
            city,
            zip_code,
        )
        if country_code and country_code == "RO":
            if not partner.is_company or name:
                if not partner.vat:
                    partner.vat = vat
                partner.is_company = True
                partner.ro_vat_change()
                partner.check_vat_on_payment()
        return partner, logs

    def _import_retrieve_partner_vals(self, tree, role):
        vals = super()._import_retrieve_partner_vals(tree, role)
        name = self._find_value(
            f"//cac:Accounting{role}Party/cac:Party//cac:PartyLegalEntity//cbc:RegistrationName",  # noqa: B950
            tree,
        )
        if name:
            vals["name"] = name
        return vals

    def _import_invoice_ubl_cii(self, invoice, file_data, new=False):
        if invoice.company_id.l10n_ro_render_anaf_pdf:
            self.l10n_ro_renderAnafPdf(invoice)
        res = super()._import_invoice_ubl_cii(invoice, file_data, new=new)
        invoice.date = invoice.invoice_date
        return res

    def l10n_ro_renderAnafPdf(self, invoice):
        attachments = self.env["ir.attachment"].search(
            [("res_model", "=", invoice._name), ("res_id", "in", invoice.ids)]
        )
        attachment = attachments.filtered(lambda x: ".xml" in x.name)
        if not attachment:
            return False
        attachment = attachment[0]

        xml_file = b64decode(attachment.datas)
        headers = {"Content-Type": "text/plain"}
        xml = xml_file
        val1 = "FACT1"
        if b"<CreditNote" in xml:
            val1 = "FCN"
        val2 = "DA"

        res = requests.post(
            f"https://webservicesp.anaf.ro/prod/FCTEL/rest/transformare/{val1}/{val2}",
            data=xml,
            headers=headers,
            timeout=25,
        )
        if "The requested URL was rejected" in res.text:
            raise UserError(_("ANAF service unable to generate PDF from this XML."))

        if res.status_code == 200:
            pdf = b64encode(res.content)
            pdf = pdf + b"=" * (len(pdf) % 3)  # Fix incorrect padding
            file_name = f"{invoice.l10n_ro_edi_transaction}.pdf"

            attachment_value = {
                "name": file_name,
                "res_id": invoice.id,
                "res_model": "account.move",
                "datas": pdf,
                "type": "binary",
                "mimetype": "application/pdf",
            }

            attachment_pdf = self.env["ir.attachment"].sudo().create(attachment_value)
            if attachments:
                invoice.with_context(no_new_invoice=True).message_post(
                    attachment_ids=attachment_pdf.ids
                )
        return res

    def _get_partner_address_vals(self, partner):
        address_vals = super()._get_partner_address_vals(partner)
        # Adaugă numele partenerului
        address_vals["partner_name"] = partner.name
        return address_vals

    def _get_partner_party_vals(self, partner, role):
        # EXTENDS account.edi.xml.ubl_21
        vals = super()._get_partner_party_vals(partner, role)

        partner = partner.commercial_partner_id

        if not partner.is_company and partner.l10n_ro_edi_ubl_no_send_cnp:
            vals["endpoint_id"] = "0000000000000"
        return vals

    def _get_partner_party_tax_scheme_vals_list(self, partner, role):
        # EXTENDS 'account_edi_ubl_cii'
        vals_list = super()._get_partner_party_tax_scheme_vals_list(partner, role)
        partner = partner.commercial_partner_id
        for vals in vals_list:
            # /!\ For Romanian companies, the company_id can be with or without country code.
            if partner.country_id.code == "RO":
                if (
                    partner.vat and not partner.vat.upper().startswith("RO")
                ) or not partner.vat:
                    vals["tax_scheme_vals"] = {"id": "!= VAT"}
                if (
                    not partner.is_company
                    and not partner.l10n_ro_edi_ubl_no_send_cnp
                    and not partner.vat
                ):
                    vals["company_id"] = "0000000000000"
                if not partner.is_company and partner.l10n_ro_edi_ubl_no_send_cnp:
                    vals["company_id"] = "0000000000000"
        return vals_list

    def _get_partner_party_legal_entity_vals_list(self, partner):
        val_list = super()._get_partner_party_legal_entity_vals_list(partner)
        partner = partner.commercial_partner_id
        if (
            not partner.is_company
            and not partner.l10n_ro_edi_ubl_no_send_cnp
            and not partner.vat
        ):
            for vals in val_list:
                if vals.get("commercial_partner") == partner:
                    vals["company_id"] = "0000000000000"
        if partner.vat and partner.l10n_ro_edi_ubl_no_send_cnp:
            for vals in val_list:
                if vals.get("commercial_partner") == partner:
                    vals["company_id"] = "0000000000000"
        return val_list

    def split_string(self, string):
        return [string[i : i + 100] for i in range(0, len(string), 100)]

    def _export_invoice_constraints(self, invoice, vals):
        # EXTENDS 'account_edi_ubl_cii'
        constraints = super()._export_invoice_constraints(invoice, vals)
        partner = vals["customer"]
        if not partner.is_company:
            constraints.pop("ciusro_customer_tax_identifier_required", False)
        return constraints


class AccountEdiCommon(models.AbstractModel):
    _inherit = "account.edi.common"

    def _check_required_fields(self, record, field_names, custom_warning_message=""):
        """
        For fizical persons if they have the l10n_ro_edi_ubl_no_send_cnp
        checked, we don't need to check the VAT field"""
        if isinstance(record, models.Model) and record._name == "res.partner":
            if not record.is_company and record.l10n_ro_edi_ubl_no_send_cnp:
                if not isinstance(field_names, list):
                    field_names = [field_names]
                if "vat" in field_names:
                    field_names = [field for field in field_names if field != "vat"]
        if not field_names:
            return
        return super()._check_required_fields(
            record, field_names, custom_warning_message
        )
