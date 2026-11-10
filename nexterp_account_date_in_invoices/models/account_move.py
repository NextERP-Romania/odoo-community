# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from datetime import timedelta

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_accounting_date(self, invoice_date, has_tax, lock_dates=None):
        """Get either invoice_date or tax_lock_date + 1"""
        acc_date = super()._get_accounting_date(invoice_date, has_tax, lock_dates)
        # Only Romanian companies override the accounting date with the invoice
        # date; for any other company keep core's (lock-date-aware) result.
        if self.company_id.account_fiscal_country_id.code != "RO":
            return acc_date
        tax_lock_date = self.company_id.tax_lock_date
        if invoice_date and tax_lock_date and has_tax and invoice_date <= tax_lock_date:
            invoice_date = tax_lock_date + timedelta(days=1)
        if self.is_purchase_document(include_receipts=True):
            acc_date = invoice_date
        return acc_date
