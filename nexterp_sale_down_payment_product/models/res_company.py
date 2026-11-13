# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_ro_sale_down_payment_product_id = fields.Many2one(
        "product.product",
        string="Sale Down Payment Product",
        domain=[("type", "=", "service")],
        check_company=True,
        help="Product set on the down payment lines of sale orders "
        "and on the down payment invoice lines.",
    )
