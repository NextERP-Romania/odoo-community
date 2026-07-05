# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import fields, models

from odoo.addons.account.models.product import ACCOUNT_DOMAIN


class ProductTemplate(models.Model):
    _inherit = "product.template"

    property_account_production_wip_account_id = fields.Many2one(
        "account.account",
        "WIP Production Account",
        company_dependent=True,
        ondelete="restrict",
        domain=ACCOUNT_DOMAIN,
        check_company=True,
        help="""This account will be used as a WIP Production Account.""",
    )

    property_account_production_wip_overhead_account_id = fields.Many2one(
        "account.account",
        "WIP Production Account Counterpart",
        company_dependent=True,
        ondelete="restrict",
        domain=ACCOUNT_DOMAIN,
        check_company=True,
        help="""This account will be used as a WIP Production Account Counterpart.""",
    )

    def _get_product_accounts(self):
        accounts = super()._get_product_accounts()

        company = (
            self.env["res.company"].browse(self.env.context.get("force_company"))
            or self.env.company
        )
        if not company.l10n_ro_accounting:
            return accounts
        prod_wip_account = (
            self.property_account_production_wip_account_id
            or self.categ_id.property_account_production_wip_account_id
            or company.account_production_wip_account_id
        )
        prod_wip_overhead_account = (
            self.property_account_production_wip_overhead_account_id
            or self.categ_id.property_account_production_wip_overhead_account_id
            or company.account_production_wip_overhead_account_id
        )
        accounts.update(
            {
                "production_wip": prod_wip_account,
                "production_wip_overhead": prod_wip_overhead_account,
            }
        )
        return accounts
