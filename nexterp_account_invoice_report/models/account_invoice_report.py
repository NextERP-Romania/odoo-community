# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

from odoo import api, models


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        res = super().read_group(
            domain,
            fields,
            groupby,
            offset=offset,
            limit=limit,
            orderby=orderby,
            lazy=lazy,
        )
        if "quantity:sum" not in fields:
            return res
        for line in res:
            if line["quantity"] != 0:
                line["price_average"] = line["price_subtotal"] / line["quantity"]
        return res
