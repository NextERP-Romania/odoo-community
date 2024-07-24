# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

from odoo import models
from odoo.tools.sql import column_exists, create_column


class SaleOrder(models.Model):
    _name = "sale.order"
    _inherit = ["sale.order", "base.inter.company"]

    def _auto_init(self):
        """
        Create compute stored field is_inter_company
        here to avoid MemoryError on large databases.
        """
        if not column_exists(self.env.cr, "sale_order", "is_inter_company"):
            create_column(self.env.cr, "sale_order", "is_inter_company", "boolean")
            company_partners = self.env["res.company"].search([]).mapped("partner_id")
            company_partners_ids = company_partners.mapped("id")
            # pylint: disable=E8103
            self.env.cr.execute(
                f"""
                WITH so_link AS (
                    SELECT
                        so.id AS id,
                        com_partner.id as partner_id,
                        company_partner.id AS company_partner_id
                    FROM sale_order so
                        LEFT JOIN res_partner com_partner
                            ON com_partner.id = so.partner_id
                        LEFT JOIN res_company company
                            ON company.id = so.company_id
                        LEFT JOIN res_partner company_partner
                            ON company_partner.id = company.partner_id
                    GROUP BY so.id, com_partner.id, company_partner.id
                )
                UPDATE sale_order so
                SET is_inter_company =
                    CASE
                        WHEN so_link.partner_id = ANY(ARRAY{company_partners_ids})
                            AND so_link.partner_id <> so_link.company_partner_id
                                THEN TRUE
                        ELSE FALSE
                    END
                FROM so_link
                WHERE so.id = so_link.id;"""
            )  # noqa
        return super()._auto_init()
