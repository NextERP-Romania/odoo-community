# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import fields, models
from odoo.tools.sql import column_exists, create_column


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    _name = "sale.order.line"

    is_inter_company = fields.Boolean(
        related="order_id.is_inter_company", store=True, readonly=True, index=True
    )

    def _auto_init(self):
        """
        Create compute stored field is_inter_company
        here to avoid MemoryError on large databases.
        """
        if not column_exists(self.env.cr, "sale_order_line", "is_inter_company"):
            create_column(self.env.cr, "sale_order_line", "is_inter_company", "boolean")
            company_partners = self.env["res.company"].search([]).mapped("partner_id")
            company_partners.mapped("id")
            company_partners.mapped("vat")
            self.env.cr.execute(
                """
                UPDATE sale_order_line sol
                SET is_inter_company = so.is_inter_company
                FROM sale_order so
                WHERE sol.order_id = so.id;
                """,
            )
        return super()._auto_init()
