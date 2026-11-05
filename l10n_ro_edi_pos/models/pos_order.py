# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    l10n_ro_fiscal_receipt_number = fields.Char(
        string="Fiscal Receipt Number",
        readonly=True,
        copy=False,
        index="btree_not_null",
        help="Number of the fiscal receipt the register printed for this order, "
        "written by the register's driver. Empty when no fiscal receipt was "
        "printed -- a point of sale without a register, or one that sells on "
        "invoice only.",
    )
