# Copyright 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

from odoo import fields, models


class AccountAnalyticDistributionModel(models.Model):
    _inherit = "account.analytic.distribution.model"

    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        ondelete="cascade",
        check_company=True,
        index=True,
        help="Pin this distribution model to a specific journal. The "
             "matching engine adds 1 to the score when the line's "
             "journal matches; if a line on a different journal hits "
             "this model, the model is excluded from the score.",
    )
