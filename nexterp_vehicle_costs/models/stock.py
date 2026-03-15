# Copyright (C) 2014 Forest AND Biomass Romania SA
# Copyright (C) 2019 OdooERP Romania SRL
# Copyright (C) 2021 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        copy=False,
    )
    refuel = fields.Boolean(copy=False)
    cost_ids = fields.One2many(
        "fleet.vehicle.log.services", "stock_move_id", string="Vehicle Costs"
    )

    fleet_service_type_id = fields.Many2one(
        "fleet.service.type", string="Vehicle Service Type"
    )

    def create_vehicle_cost(self):
        self.ensure_one()

        subtype = self.fleet_service_type_id
        cost_type = "services"
        model = self.env["fleet.vehicle.log.services"]

        if self.fleet_service_type_id.category == "Contract":
            cost_type = "contract"
            model = self.env["fleet.vehicle.log.contract"]
        elif self.fleet_service_type_id.name == "Realimentare":
            cost_type = "fuel"
            model = self.env["fleet.vehicle.log.services"]
        else:
            cost_type = "services"
            model = self.env["fleet.vehicle.log.services"]

        sub_cost = {
            "vehicle_id": self.vehicle_id.id,
            "service_type_id": subtype and subtype.id,
            "product_id": self.product_id.id,
            "amount": -self.value,
            "purchaser_id": self.create_uid.partner_id.id,
            "vendor_id": self.partner_id.id,
            "date": self.date,
            "notes": self.name,
        }

        if cost_type == "fuel":
            sub_cost["liter"] = -self.quantity
            sub_cost["service_type_id"] = self.fleet_service_type_id.id
        elif cost_type == "services":
            sub_cost["service_type_id"] = self.fleet_service_type_id.id

        sub_cost["quantity"] = -self.quantity
        sub_cost["price_unit"] = self.unit_cost
        sub_cost["stock_move_id"] = self.id

        model.create(sub_cost)

    def cancel_vehicle_cost(self):
        for s in self.cost_ids:
            s.unlink()

    def _action_done(self, cancel_backorder=False):
        for move in self:
            if (
                move.l10n_ro_nondeductible_usage
                and move.vehicle_id.not_deductible
                and not move.l10n_ro_nondeductible_tax_id
            ):
                if move.vehicle_id.l10n_ro_nondeductible_percent:
                    move.l10n_ro_nondeductible_percent = (
                        move.vehicle_id.l10n_ro_nondeductible_percent
                    )
                    move.l10n_ro_nondeductible_tax_id = (
                        move.vehicle_id.tax_non_deductible
                    )
        res = super()._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            if (
                move.vehicle_id
                and not move.cost_ids
                and move.location_dest_id.usage in ["consume", "usage_giving"]
            ):
                move.create_vehicle_cost()
        return res

    def action_cancel(self):
        res = super().action_cancel()
        for move in self:
            if move.vehicle_id and move.cost_ids:
                move.cancel_vehicle_cost()
        return res
