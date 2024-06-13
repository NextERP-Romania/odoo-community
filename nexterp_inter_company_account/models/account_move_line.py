# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import fields, models
from odoo.tools.sql import column_exists, create_column


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _name = "account.move.line"

    is_inter_company = fields.Boolean(
        related="move_id.is_inter_company", store=True, readonly=True, index=True
    )

    def _auto_init(self):
        """
        Create compute stored field is_inter_company
        here to avoid MemoryError on large databases.
        """
        if not column_exists(self.env.cr, "account_move", "is_inter_company"):
            create_column(self.env.cr, "account_move", "is_inter_company", "boolean")
            company_partners = self.env["res.company"].search([]).mapped("partner_id")
            company_partners.mapped("id")
            company_partners.mapped("vat")
            self.env.cr.execute(
                """
                UPDATE account_move_line aml
                SET is_inter_company = am.is_inter_company
                FROM account_move am
                WHERE aml.move_id = am.id;
                """,
            )
        return super()._auto_init()
