# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"

    is_inter_company = fields.Boolean(readonly=False)

    def _select_additional_fields(self):
        res = super()._select_additional_fields()
        res["is_inter_company"] = "l.is_inter_company"
        return res

    def _group_by_sale(self):
        group_by = super()._group_by_sale()
        group_by = f"""
            {group_by},
            l.is_inter_company"""
        return group_by
