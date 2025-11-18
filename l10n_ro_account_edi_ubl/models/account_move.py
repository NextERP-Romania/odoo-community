# Copyright (C) 2022 Dorin Hongu <dhongu(@)gmail(.)com
# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from datetime import timedelta

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import math

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_ro_edi_transaction = fields.Char(
        "Transaction ID (RO)",
        help="Technical field used to track the status of a submission.",
        copy=False,
        compute="_compute_l10n_ro_edi_fields",
        store=True,
    )
    l10n_ro_edi_download = fields.Char(
        "ID Download ANAF (RO)",
        help="ID used to download the ZIP file from ANAF.",
        copy=False,
    )

    l10n_ro_show_edi_fields = fields.Boolean(
        compute="_compute_l10n_ro_show_edi_fields",
        string="Show ANAF EDI Fields",
    )
    l10n_ro_edi_fields_readonly = fields.Boolean(
        compute="_compute_l10n_ro_show_edi_fields",
        string="Make ANAF EDI Fields readonly",
    )

    l10n_ro_show_anaf_download_edi_buton = fields.Boolean(
        compute="_compute_l10n_ro_show_anaf_download_edi_buton",
        string="Show ANAF Download EDI Button",
    )

    l10n_ro_edi_previous_transaction = fields.Char(
        "Previous Transactions or Download (RO)",
        help="Technical field used to track previous transactions or "
        "download ID's received from ANAF. Useful in case the invoice "
        "was sent and had errors, we could find the invoice based on "
        "old data, since on reset to draft they are removed.",
        copy=False,
    )

    @api.constrains("l10n_ro_edi_download")
    def _check_unique_edi_download_number(self):
        moves = self.filtered(lambda m: m.l10n_ro_edi_download)
        if not moves:
            return

        self.flush_model(["l10n_ro_edi_download"])

        self._cr.execute(
            """
            SELECT move2.id, move2.name
            FROM account_move move
            INNER JOIN account_move move2 ON
                move2.l10n_ro_edi_download = move.l10n_ro_edi_download
            WHERE move.id IN %s and move2.id != move.id
        """,
            [tuple(moves.ids)],
        )
        res = self._cr.fetchall()
        if res:
            raise ValidationError(
                _(
                    "You already have one invoice with the same ANAF download.\n"
                    "Invoice(s) Ids: %(ids)s\n"
                    "Invoice(s) Numbers: %(numbers)s\n"
                )
                % {
                    "ids": ", ".join(str(r[0]) for r in res),
                    "numbers": ", ".join(r[1] for r in res),
                }
            )

    @api.depends("l10n_ro_edi_state", "l10n_ro_edi_document_ids")
    def _compute_l10n_ro_edi_fields(self):
        for invoice in self:
            key_loading_docs = invoice.l10n_ro_edi_document_ids.filtered(
                lambda doc: doc.key_loading
            )
            if key_loading_docs:
                invoice.l10n_ro_edi_transaction = key_loading_docs[0].key_loading

    @api.depends("l10n_ro_edi_document_ids", "state", "l10n_ro_edi_download")
    def _compute_l10n_ro_show_edi_fields(self):
        for invoice in self:
            show_fields = readonly_fields = False
            if invoice.l10n_ro_edi_document_ids:
                if invoice.l10n_ro_edi_transaction:
                    show_fields = True
                    readonly_fields = True
            else:
                if (
                    invoice.move_type in ("in_invoice", "in_refund")
                    and not invoice.is_l10n_ro_autoinvoice()
                    and invoice.company_id.country_code == "RO"
                ):
                    show_fields = True
                    readonly_fields = True if invoice.state == "posted" else False
            invoice.l10n_ro_show_edi_fields = show_fields
            invoice.l10n_ro_edi_fields_readonly = readonly_fields

    @api.depends("l10n_ro_edi_download", "move_type")
    def _compute_l10n_ro_show_anaf_download_edi_buton(self):
        for invoice in self:
            show_button = False
            if (
                invoice.l10n_ro_edi_download
                and invoice.move_type in ("in_invoice", "in_refund")
                and not invoice.line_ids
            ):
                show_button = True
            invoice.l10n_ro_show_anaf_download_edi_buton = show_button

    def is_l10n_ro_autoinvoice(self):
        return (
            self.is_purchase_document()
            and self.journal_id.l10n_ro_sequence_type == "autoinv2"
            and self.journal_id.l10n_ro_partner_id
            and self.journal_id.l10n_ro_partner_id.ubl_cii_format == "ciusro"
        )

    def _need_ubl_cii_xml(self):
        self.ensure_one()
        if (
            not self.invoice_pdf_report_id
            and not self.ubl_cii_xml_id
            and self.is_l10n_ro_autoinvoice()
        ):
            return True
        return super()._need_ubl_cii_xml()

    def _l10n_ro_edi_create_document_invoice_sending_failed(
        self, message, attachment_raw=None, key_loading=None
    ):
        res = super()._l10n_ro_edi_create_document_invoice_sending_failed(
            message, attachment_raw, key_loading
        )
        if message:
            self.l10n_ro_edi_post_message(self, message, res)
        return res

    @api.model
    def l10n_ro_edi_post_message(self, invoice, message, res):
        body = message
        if "error" in res.message:
            body += _("\n\nError:\n<p>%s</p>") % res["error"]
        users = (
            invoice.company_id.l10n_ro_edi_error_notify_users or invoice.invoice_user_id
        )
        for user in users:
            mail_activity = invoice.activity_ids.filtered(
                lambda a: a.summary == message and a.user_id == user
            )
            if mail_activity:
                mail_activity.write(
                    {
                        "date_deadline": fields.Date.today(),
                        "note": body,
                    }
                )
            else:
                invoice.activity_schedule(
                    "mail.mail_activity_data_warning",
                    summary=message,
                    note=body,
                    user_id=user.id,
                )

    def write(self, vals):
        if vals.get("l10n_ro_edi_download"):
            self.l10n_ro_complete_old_transaction(vals["l10n_ro_edi_download"])
        if vals.get("l10n_ro_edi_transaction"):
            self.l10n_ro_complete_old_transaction(vals["l10n_ro_edi_transaction"])
        res = super().write(vals)
        return res

    def l10n_ro_complete_old_transaction(self, old_transaction):
        if not old_transaction:
            return
        for move in self:
            if not move.l10n_ro_edi_previous_transaction:
                move.l10n_ro_edi_previous_transaction = old_transaction
            elif old_transaction not in move.l10n_ro_edi_previous_transaction:
                move.l10n_ro_edi_previous_transaction += f", {old_transaction}"

    def _l10n_ro_edi_fetch_invoice_sending_documents(self):
        """
        Inherit to store key download to the invoice
        """
        res = super()._l10n_ro_edi_fetch_invoice_sending_documents()

        session = requests.Session()
        invoices_to_fetch = self.filtered(
            lambda inv: inv.l10n_ro_edi_state == "invoice_sent"
            and not inv.l10n_ro_edi_download
        )

        for invoice in invoices_to_fetch:
            result = self.env["l10n_ro_edi.document"]._request_ciusro_fetch_status(
                company=invoice.company_id,
                key_loading=invoice.l10n_ro_edi_transaction,
                session=session,
            )
            if result.get("key_download"):
                invoice.l10n_ro_edi_download = result["key_download"]
        return res

    def l10n_ro_download_zip_anaf(self):
        for invoice in self:
            if not invoice.l10n_ro_edi_download:
                continue
            result = self.env["l10n_ro_edi.document"]._request_ciusro_download_zipfile(
                company=invoice.company_id,
                key_download=invoice.l10n_ro_edi_download,
                session=requests,
            )
            active_sending_document = invoice.l10n_ro_edi_document_ids.filtered(
                lambda d: d.state == "invoice_sending"
            )
            if active_sending_document:
                active_sending_document = active_sending_document[0]
                previous_raw = active_sending_document.attachment_id.sudo().raw
                if "error" in result:
                    invoice._l10n_ro_edi_create_document_invoice_sending_failed(
                        result["error"], previous_raw
                    )
            attachment = (
                self.env["ir.attachment"]
                .sudo()
                .create(
                    self._l10n_ro_edi_create_attachment_values(result["attachment_raw"])
                )
            )
            if invoice.invoice_line_ids:
                raise UserError(
                    _(
                        "The invoice already have invoice lines, "
                        "you cannot update them again from the XMl downloaded file."
                    )
                )
            invoice._extend_with_attachments(attachment)

    @api.model
    def _get_ubl_cii_builder_from_xml_tree(self, tree):
        customization_id = tree.find("{*}CustomizationID")
        if customization_id is not None and "CIUS-RO" in customization_id.text:
            return self.env["account.edi.xml.ubl_ro"]
        return super()._get_ubl_cii_builder_from_xml_tree(tree)

    def _generate_pdf_and_send_invoice(
        self,
        template,
        force_synchronous=True,
        allow_fallback_pdf=True,
        bypass_download=False,
        **kwargs,
    ):
        if self.env.context.get("test_data"):
            return self.env.context["test_data"]
        res = super()._generate_pdf_and_send_invoice(
            template, force_synchronous, allow_fallback_pdf, bypass_download, **kwargs
        )
        return res

    def template_send_email_invoice(self):
        template = self.env.ref(
            "account.email_template_edi_invoice",
            raise_if_not_found=False,
        )
        return template

    def send_email_invoice_anaf(self):
        template = self.template_send_email_invoice()
        company_ids = (
            self.env["res.company"]
            .sudo()
            .search(
                [
                    ("l10n_ro_edi_access_token", "!=", False),
                    ("l10n_ro_edi_residence", "!=", False),
                ]
            )
        )
        for company in company_ids:
            days = company.l10n_ro_edi_residence
            date = fields.Date.today() - timedelta(days=days)
            invoices = self.env["account.move"].search(
                [
                    ("l10n_ro_edi_state", "=", False),
                    ("move_type", "!=", "entry"),
                    ("state", "=", ("posted")),
                    ("invoice_date", "<=", date),
                    ("country_code", "=", "RO"),
                    ("company_id", "=", company.id),
                ]
            )
            invoices = invoices.filtered(lambda l: l._need_ubl_cii_xml())
            composer = (
                self.env["account.move.send"]
                .with_context(active_model="account.move", active_ids=invoices.ids)
                .create(
                    {
                        "mail_template_id": template.id,
                        "checkbox_download": False,
                        "checkbox_send_mail": False,
                    }
                )
            )
            composer.action_send_and_print(force_synchronous=False)

    def fetch_invoice_anaf(self):
        invoices = self.env["account.move"].search(
            [("l10n_ro_edi_state", "=", "invoice_sending"), ("country_code", "=", "RO")]
        )
        if invoices:
            invoices._l10n_ro_edi_fetch_invoice_sending_documents()

    def _is_l10n_ro_b2c(self):
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        return partner.country_id.code == "RO" and not partner.is_company

    def _l10n_ro_edi_send_invoice(self, xml_data):
        self.ensure_one()
        # Add context in case of b2c invoices
        if self._is_l10n_ro_b2c():
            self = self.with_context(l10n_ro_edi_b2c=True)
        return super()._l10n_ro_edi_send_invoice(xml_data)
    
    def _prepare_invoice_aggregated_taxes(self, filter_invl_to_apply=None, filter_tax_values_to_apply=None, grouping_key_generator=None):
        self.ensure_one()
        if self.company_id.country_code != 'RO':
            return super()._prepare_invoice_aggregated_taxes(
                filter_invl_to_apply=filter_invl_to_apply,
                filter_tax_values_to_apply=filter_tax_values_to_apply,
                grouping_key_generator=grouping_key_generator,
            )

        base_lines = [
            x._convert_to_tax_base_line_dict()
            for x in self.line_ids.filtered(lambda x: x.display_type == 'product' and (not filter_invl_to_apply or filter_invl_to_apply(x)))
        ]

        to_process = []
        for base_line in base_lines:
            to_update_vals, tax_values_list = self.env['account.tax']._compute_taxes_for_single_line(base_line)
            to_process.append((base_line, to_update_vals, tax_values_list))
        tax_lines = self._get_tax_lines_to_aggregate()
        sign = -1 if self.is_inbound(include_receipts=True) else 1

        # Collect the tax_amount_currency/balance from tax lines.
        current_tax_amount_per_rep_line = {}
        for tax_line in tax_lines:
            tax_rep_amounts = current_tax_amount_per_rep_line.setdefault(tax_line.tax_repartition_line_id.id, {
                'tax_amount_currency': 0.0,
                'tax_amount': 0.0,
            })
            tax_rep_amounts['tax_amount_currency'] += sign * tax_line.amount_currency
            tax_rep_amounts['tax_amount'] += sign * tax_line.balance

        # Collect the computed tax_amount_currency/tax_amount from the taxes computation.
        tax_details_per_rep_line = {}
        for _base_line, _to_update_vals, tax_values_list in to_process:
            for tax_values in tax_values_list:
                tax_rep_id = tax_values['tax_repartition_line_id']
                tax_rep_amounts = tax_details_per_rep_line.setdefault(tax_rep_id, {
                    'tax_amount_currency': 0.0,
                    'tax_amount': 0.0,
                    'distribute_on': [],
                })
                tax_rep_amounts['tax_amount_currency'] += tax_values['tax_amount_currency']
                tax_rep_amounts['tax_amount'] += tax_values['tax_amount']
                tax_rep_amounts['distribute_on'].append(tax_values)

        # Dispatch the delta on tax_values.
        for key, currency in (('tax_amount_currency', self.currency_id), ('tax_amount', self.company_currency_id)):
            for tax_rep_id, computed_tax_rep_amounts in tax_details_per_rep_line.items():
                current_tax_rep_amounts = current_tax_amount_per_rep_line.get(tax_rep_id, computed_tax_rep_amounts)
                diff = current_tax_rep_amounts[key] - computed_tax_rep_amounts[key]
                abs_diff = abs(diff)

                if currency.is_zero(abs_diff):
                    continue

                diff_sign = -1 if diff < 0 else 1
                nb_error = math.ceil(abs_diff / currency.rounding)
                nb_cents_per_tax_values = math.floor(nb_error / len(computed_tax_rep_amounts['distribute_on']))
                nb_extra_cent = nb_error % len(computed_tax_rep_amounts['distribute_on'])
                for tax_values in computed_tax_rep_amounts['distribute_on']:

                    if currency.is_zero(abs_diff):
                        break

                    nb_amount_curr_cent = nb_cents_per_tax_values
                    if nb_extra_cent:
                        nb_amount_curr_cent += 1
                        nb_extra_cent -= 1

                    # We can have more than one cent to distribute on a single tax_values.
                    abs_delta_to_add = min(abs_diff, currency.rounding * nb_amount_curr_cent)
                    tax_values[key] += diff_sign * abs_delta_to_add
                    abs_diff -= abs_delta_to_add

        return self.env['account.tax'].with_company(self.company_id)._aggregate_taxes(
            to_process,
            filter_tax_values_to_apply=filter_tax_values_to_apply,
            grouping_key_generator=grouping_key_generator,
        )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _compute_all_tax(self):
        invoices = self.mapped("move_id").filtered(
            lambda l: l.company_id.country_code == "RO" and l.move_type != "entry"
        )
        for invoice in invoices:
            if (
                "on_payment"
                in invoice.line_ids.tax_ids.flatten_taxes_hierarchy().mapped(
                    "tax_exigibility"
                )
            ):
                invoice.always_tax_exigible = True
        return super()._compute_all_tax()
