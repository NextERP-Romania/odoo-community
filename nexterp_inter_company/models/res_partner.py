# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

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
        for record in self:
            is_inter_company = False
            record_companies = self.env["res.company"].search([('partner_id', '=', record.id)])
            if record_companies:
                is_inter_company = True
            record.is_inter_company = is_inter_company

    def _auto_init(self):
        """
        Create compute stored field is_inter_company
        here to avoid MemoryError on large databases.
        """
        if not column_exists(self.env.cr, "res_partner", "is_inter_company"):
            create_column(self.env.cr, "res_partner", "is_inter_company", "boolean")
            company_partners = self.env["res.company"].search([]).mapped("partner_id")
            # pylint: disable=E8103
            self.env.cr.execute(
                """
                UPDATE res_partner am
                SET is_inter_company = FALSE;
                """
            )  # noqa
            for company in self.env["res.company"].search([]):
                partners = company_partners.filtered(
                    lambda p: p.id == company.partner_id.id
                )
                # pylint: disable=E8103
                self.env.cr.execute(
                    """
                    UPDATE res_partner am
                    SET is_inter_company = True
                    WHERE id = ANY(ARRAY%s);"""
                    % (partners.ids)
                )  # noqa
        return super()._auto_init()