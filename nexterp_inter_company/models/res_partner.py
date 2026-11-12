# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import fields, models
from odoo.tools.sql import column_exists, create_column


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_inter_company = fields.Boolean(
        compute="_compute_is_inter_company",
        readonly=False,
        store=True,
        index=True,
        help="The field computes if the record represent a "
        "inter company transaction or not.",
    )

    def _compute_is_inter_company(self):
        # One query for the whole batch. The field is stored and has no
        # depends, so it is computed on every partner that gets created: a
        # search per record turned a contact import into a query per line.
        #
        # Read the companies with elevated rights on purpose: whether a
        # partner is a company of this database is a fact about the database,
        # not about who is looking. Searching as the user made a stored field
        # depend on the companies that user happens to be allowed to see, so
        # the same partner was marked or not depending on who saved it.
        stored_ids = [pid for pid in self.ids if isinstance(pid, int)]
        company_partner_ids = set()
        if stored_ids:
            company_partner_ids = set(
                self.env["res.company"]
                .sudo()
                .search([("partner_id", "in", stored_ids)])
                .partner_id.ids
            )
        for record in self:
            record.is_inter_company = record.id in company_partner_ids

    def _auto_init(self):
        """
        Create compute stored field is_inter_company
        here to avoid MemoryError on large databases.
        """
        if not column_exists(self.env.cr, "res_partner", "is_inter_company"):
            create_column(self.env.cr, "res_partner", "is_inter_company", "boolean")
            # pylint: disable=no-search-all
            company_partners = self.env["res.company"].search([]).mapped("partner_id")
            # pylint: disable=E8103
            self.env.cr.execute(
                """
                UPDATE res_partner am
                SET is_inter_company = FALSE;
                """
            )  # noqa
            for company in self.env["res.company"].search([]):  # pylint: disable=no-search-all
                partners = company_partners.filtered(
                    lambda p, company=company: p.id == company.partner_id.id
                )
                # pylint: disable=E8103
                self.env.cr.execute(
                    f"""
                    UPDATE res_partner am
                    SET is_inter_company = True
                    WHERE id = ANY(ARRAY{partners.ids});"""
                )  # noqa
        return super()._auto_init()
