# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

from odoo import models
from odoo.tools.sql import column_exists, create_column


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "base.inter.company"]

    def _auto_init(self):
        """
        Create compute stored field is_inter_company
        here to avoid MemoryError on large databases.
        """
        if not column_exists(self.env.cr, "account_move", "is_inter_company"):
            create_column(self.env.cr, "account_move", "is_inter_company", "boolean")
            company_partners = self.env["res.company"].search([]).mapped("partner_id")
            # pylint: disable=E8103
            self.env.cr.execute(
                """
                UPDATE account_move am
                SET is_inter_company = FALSE;
                """
            )  # noqa
            for company in self.env["res.company"].search([]):
                partners = company_partners.filtered(
                    lambda p: p.id != company.partner_id.id
                )
                # pylint: disable=E8103
                self.env.cr.execute(
                    f"""
                    UPDATE account_move am
                    SET is_inter_company = True
                    WHERE am.partner_id = ANY(ARRAY{partners.ids});"""
                )  # noqa
        return super()._auto_init()
