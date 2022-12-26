# Copyright (C) 2014 Forest AND Biomass Romania SA
# Copyright (C) 2019 OdooERP Romania SRL
# Copyright (C) 2021 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    vehicle_contract = fields.Boolean(
        string="Generate Vehicle Contract",
        copy=False,
        help="Ticking this field will enable vehicle "
        "contract generation on supplier invoices "
        "automatically",
    )
