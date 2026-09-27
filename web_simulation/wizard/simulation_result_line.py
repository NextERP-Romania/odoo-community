# Copyright (C) 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
"""The lines of a simulation result.

They are transient, and they are written after the flow has been rolled
back, so they describe records that no longer exist.  That is why they hold
copies of what mattered rather than links to it.
"""

from odoo import api, fields, models


class SimulationResultDocument(models.TransientModel):
    _name = "web.simulation.result.document"
    _description = "Simulated Document"
    _order = "sequence, id"

    report_id = fields.Many2one(
        "web.simulation.result", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(readonly=True)
    model_name = fields.Char(readonly=True)
    model_description = fields.Char(string="Kind", readonly=True)
    res_id = fields.Integer(readonly=True)
    name = fields.Char(string="Document", readonly=True)
    state = fields.Char(string="Status", readonly=True)
    amount = fields.Float(readonly=True)


class SimulationResultMove(models.TransientModel):
    _name = "web.simulation.result.move"
    _description = "Simulated Stock Move"
    _order = "id"

    report_id = fields.Many2one(
        "web.simulation.result", required=True, ondelete="cascade"
    )
    reference = fields.Char(string="Document", readonly=True)
    product_id = fields.Many2one("product.product", readonly=True)
    location_id = fields.Many2one("stock.location", string="From", readonly=True)
    location_dest_id = fields.Many2one("stock.location", string="To", readonly=True)
    quantity = fields.Float(readonly=True)
    uom_name = fields.Char(string="UoM", readonly=True)
    value = fields.Float(readonly=True)


class SimulationResultQuant(models.TransientModel):
    _name = "web.simulation.result.quant"
    _description = "Simulated Stock Balance"
    _order = "product_id, location_id, id"

    report_id = fields.Many2one(
        "web.simulation.result", required=True, ondelete="cascade"
    )
    product_id = fields.Many2one("product.product", readonly=True)
    location_id = fields.Many2one("stock.location", readonly=True)
    lot_name = fields.Char(string="Lot/Serial", readonly=True)
    quantity_before = fields.Float(string="Before", readonly=True)
    quantity_change = fields.Float(string="Change", readonly=True)
    quantity = fields.Float(string="On Hand", readonly=True)
    uom_name = fields.Char(string="UoM", readonly=True)
    value = fields.Float(readonly=True)


class SimulationResultAccount(models.TransientModel):
    _name = "web.simulation.result.account"
    _description = "Simulated Journal Item"
    _order = "move_name, id"

    report_id = fields.Many2one(
        "web.simulation.result", required=True, ondelete="cascade"
    )
    move_name = fields.Char(string="Journal Entry", readonly=True)
    move_state = fields.Char(string="Status", readonly=True)
    date = fields.Date(readonly=True)
    account_id = fields.Many2one("account.account", readonly=True)
    name = fields.Char(string="Label", readonly=True)
    partner_id = fields.Many2one("res.partner", readonly=True)
    debit = fields.Float(readonly=True)
    credit = fields.Float(readonly=True)


class SimulationResultAccountSummary(models.TransientModel):
    _name = "web.simulation.result.account.summary"
    _description = "Simulated Account Total"
    _order = "account_code, id"

    report_id = fields.Many2one(
        "web.simulation.result", required=True, ondelete="cascade"
    )
    account_id = fields.Many2one("account.account", readonly=True)
    account_code = fields.Char(related="account_id.code", store=True, string="Code")
    debit = fields.Float(readonly=True)
    credit = fields.Float(readonly=True)
    balance = fields.Float(compute="_compute_balance")

    @api.depends("debit", "credit")
    def _compute_balance(self):
        for line in self:
            line.balance = line.debit - line.credit
