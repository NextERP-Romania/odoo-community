# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import fields, models

from odoo.addons.account.models.product import ACCOUNT_DOMAIN


class ProductCategory(models.Model):
    _inherit = "product.category"

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
        "WIP Production Account Overhead",
        company_dependent=True,
        ondelete="restrict",
        domain=ACCOUNT_DOMAIN,
        check_company=True,
        help="""This account will be used as a WIP Production Account Overhead.""",
    )
