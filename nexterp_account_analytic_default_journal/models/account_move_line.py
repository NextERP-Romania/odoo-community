# Copyright (C) 2023 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _compute_analytic_account_id(self):
        found_with_journal = self.env['account.move.line']
        for record in self:
            if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
                rec = self.env['account.analytic.default'].account_get(
                    product_id=record.product_id.id,
                    partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
                    account_id=record.account_id.id,
                    user_id=record.env.uid,
                    date=record.date,
                    company_id=record.move_id.company_id.id,
                    journal_id=record.journal_id.id
                )
                if rec:
                    record.analytic_account_id = rec.analytic_id
                    found_with_journal |= record
        super(AccountMoveLine, self - found_with_journal)._compute_analytic_account_id(
        

    def _compute_analytic_tag_ids(self):
        found_with_journal = self.env['account.move.line']
        for record in self:
            if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
                rec = self.env['account.analytic.default'].account_get(
                    product_id=record.product_id.id,
                    partner_id=record.partner_id.commercial_partner_id.id or record.move_id.partner_id.commercial_partner_id.id,
                    account_id=record.account_id.id,
                    user_id=record.env.uid,
                    date=record.date,
                    company_id=record.move_id.company_id.id,
                    journal_id=record.journal_id.id
                )
                if rec:
                    record.analytic_tag_ids = rec.analytic_tag_ids
                    found_with_journal |= record
        super(AccountMoveLine, self - found_with_journal)._compute_analytic_tag_ids()
