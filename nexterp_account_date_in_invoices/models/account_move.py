# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

from datetime import timedelta

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_accounting_date(self, invoice_date, has_tax):
        """Get either invoice_date or tax_lock_date + 1"""
        acc_date = super()._get_accounting_date(invoice_date, has_tax)
        tax_lock_date = self.company_id.tax_lock_date
        fields.Date.today()
        if invoice_date and tax_lock_date and has_tax and invoice_date <= tax_lock_date:
            invoice_date = tax_lock_date + timedelta(days=1)
        if self.is_purchase_document(include_receipts=True):
            acc_date = invoice_date
        return acc_date
