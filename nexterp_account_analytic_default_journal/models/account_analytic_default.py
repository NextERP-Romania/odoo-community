# Copyright (C) 2023 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models


class AccountAnalyticDefault(models.Model):
    _inherit = "account.analytic.default"

    journal_id = fields.Many2one("account.journal", string="Jopurnal")

    @api.model
    def account_get(
        self,
        product_id=None,
        partner_id=None,
        account_id=None,
        user_id=None,
        date=None,
        company_id=None,
        journal_id=None,
    ):
        domain = []
        if product_id:
            domain += ["|", ("product_id", "=", product_id)]
        domain += [("product_id", "=", False)]
        if partner_id:
            domain += ["|", ("partner_id", "=", partner_id)]
        domain += [("partner_id", "=", False)]
        if account_id:
            domain += ["|", ("account_id", "=", account_id)]
        domain += [("account_id", "=", False)]
        if company_id:
            domain += ["|", ("company_id", "=", company_id)]
        domain += [("company_id", "=", False)]
        if user_id:
            domain += ["|", ("user_id", "=", user_id)]
        domain += [("user_id", "=", False)]
        if date:
            domain += ["|", ("date_start", "<=", date), ("date_start", "=", False)]
            domain += ["|", ("date_stop", ">=", date), ("date_stop", "=", False)]
        if journal_id:
            domain += ["|", ("journal_id", "=", journal_id)]
        domain += [("journal_id", "=", False)]
        best_index = -1
        res = self.env["account.analytic.default"]
        for rec in self.search(domain):
            index = 0
            if rec.product_id:
                index += 1
            if rec.partner_id:
                index += 1
            if rec.account_id:
                index += 1
            if rec.company_id:
                index += 1
            if rec.user_id:
                index += 1
            if rec.journal_id:
                index += 1
            if rec.date_start:
                index += 1
            if rec.date_stop:
                index += 1
            if index > best_index:
                res = rec
                best_index = index
        return res
