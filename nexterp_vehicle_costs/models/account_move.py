# Copyright (C) 2014 Forest AND Biomass Romania SA
# Copyright (C) 2019 OdooERP Romania SRL
# Copyright (C) 2021 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).


from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    has_vehicle_contracts = fields.Boolean(compute="_compute_has_vehicle_costs")
    has_vehicle_services = fields.Boolean(compute="_compute_has_vehicle_costs")

    def _compute_has_vehicle_costs(self):
        for move in self:
            has_vehicle_contracts = False
            has_vehicle_services = False
            has_vehicle_services = False
            for line in move.line_ids:
                if line.veh_service_cost_ids:
                    has_vehicle_services = True
                if line.veh_contract_cost_ids:
                    has_vehicle_contracts = True
            move.has_vehicle_services = has_vehicle_services
            move.has_vehicle_contracts = has_vehicle_contracts

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for line in self.invoice_line_ids:
            if line.vehicle_id and not line.cost_ids:
                line.create_vehicle_cost()
        return res

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        for line in self.invoice_line_ids:
            if line.vehicle_id and line.cost_ids:
                line.cancel_vehicle_cost()
        return res

    def action_open_vehicle_service_costs(self):
        self.ensure_one()
        veh_costs = self.line_ids.mapped("veh_service_cost_ids").ids
        xml_id = "fleet_vehicle_log_services_action"
        res = self.env["ir.actions.act_window"]._for_xml_id("fleet.%s" % xml_id)
        res.update(
            context=dict(self.env.context, default_vehicle_id=self.id, group_by=False),
            domain=[("id", "in", veh_costs)],
        )
        return res

    def action_open_vehicle_contract_costs(self):
        self.ensure_one()
        veh_costs = self.line_ids.mapped("veh_contract_cost_ids").ids
        xml_id = "fleet_vehicle_log_contract_action"
        res = self.env["ir.actions.act_window"]._for_xml_id("fleet.%s" % xml_id)
        res.update(
            context=dict(self.env.context, default_vehicle_id=self.id, group_by=False),
            domain=[("id", "in", veh_costs)],
        )
        return res
