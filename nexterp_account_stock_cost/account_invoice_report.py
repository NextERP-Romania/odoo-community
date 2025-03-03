# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import models, fields


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"


    stock_cost = fields.Float(string="Stock Cost", readonly=True)
    stock_cost_product = fields.Float(string="Stock Cost Product", readonly=True)
    stock_cost_price_diff = fields.Float(string="Stock Cost Price Diff", readonly=True)
    stock_cost_additional_cost = fields.Float(string="Stock Cost Additional Cost", readonly=True)
    stock_cost_supplier_id = fields.Many2one('res.currency', string='Stock Cost Supplier', readonly=True)

    def _select(self):
        select_str = super()._select()
        select_str += """
            , line.stock_cost as stock_cost
            , line.stock_cost_product as stock_cost_product
            , line.stock_cost_price_diff as stock_cost_price_diff
            , line.stock_cost_additional_cost as stock_cost_additional_cost
            , line.stock_cost_supplier_id as stock_cost_supplier_id
            """
        return select_str
