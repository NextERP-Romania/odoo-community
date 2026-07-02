# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import fields, models


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "l10n.ro.mixin"]

    # The link to the manufacturing order reuses the native
    # ``wip_production_ids`` (mrp.production <-> account.move) provided by
    # ``mrp_account``. We only add the extra link to the work order, because
    # labour entries are not backed by a stock move and would otherwise have no
    # traceable origin. Component / finished-goods WIP entries are linked to
    # their ``stock.move`` natively (account_move_id / stock_move_ids).
    l10n_ro_wip_workorder_id = fields.Many2one(
        "mrp.workorder",
        string="WIP Work Order",
        help="The work order whose labour cost generated this WIP account move.",
    )
