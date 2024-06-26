# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import models
from odoo.tools.sql import column_exists, create_column


class AccountMove(models.Model):
    _inherit = ["account.move", "base.inter.company"]
    _name = "account.move"

    def _auto_init(self):
        """
        Create compute stored field is_inter_company
        here to avoid MemoryError on large databases.
        """
        if not column_exists(self.env.cr, "account_move", "is_inter_company"):
            create_column(self.env.cr, "account_move", "is_inter_company", "boolean")
            company_partners = self.env["res.company"].search([]).mapped("partner_id")
            company_partners_ids = company_partners.mapped("id")
            company_partners_vats = company_partners.mapped("vat")
            if company_partners_vats == [False]:
                company_partners_vats = [""]
            self.env.cr.execute(
                """
                WITH am_link AS (
                    SELECT
                        am.id AS id,
                        com_partner.id as partner_id,
                        com_partner.vat as partner_vat,
                        company_partner.vat AS company_partner_vat,
                        company_partner.id AS company_partner_id
                    FROM account_move am
                        LEFT JOIN res_partner com_partner
                            ON com_partner.id = am.commercial_partner_id
                        LEFT JOIN res_company company
                            ON company.id = am.company_id
                        LEFT JOIN res_partner company_partner
                            ON company_partner.id = company.partner_id
                    GROUP BY am.id, com_partner.id, company_partner.id
                )
                UPDATE account_move am
                SET is_inter_company =
                    CASE
                        WHEN am_link.partner_id = ANY(COALESCE(%s, ARRAY[0]))
                            AND am_link.partner_id <> am_link.company_partner_id
                                THEN TRUE
                        WHEN am_link.partner_vat = ANY(COALESCE(%s, ARRAY['']))
                            AND am_link.partner_vat <> am_link.company_partner_vat
                                THEN TRUE
                        ELSE FALSE
                    END
                FROM am_link
                WHERE am.id = am_link.id;""",
                (company_partners_ids, company_partners_vats),
            )  # noqa
        return super()._auto_init()
