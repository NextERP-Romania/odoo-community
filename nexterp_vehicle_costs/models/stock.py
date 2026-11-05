# Copyright (C) 2014 Forest AND Biomass Romania SA
# Copyright (C) 2019 OdooERP Romania SRL
# Copyright (C) 2021 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import api, fields, models
from odoo.exceptions import UserError


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
        "fleet.service.type",
        string="Vehicle Service Type",
        compute="_compute_fleet_service_type_id",
        store=True,
    )

    @api.onchange("vehicle_id")
    def _onchange_fleet_service_type_id(self):
        if self.vehicle_id.tax_non_deductible:
            self.l10n_ro_nondeductible_tax_id = self.vehicle_id.tax_non_deductible
            self.l10n_ro_nondeductible_percent = (
                self.vehicle_id.l10n_ro_nondeductible_percent
            )

    @api.depends("refuel", "vehicle_id")
    def _compute_fleet_service_type_id(self):
        fstype = self.env["fleet.service.type"]

        def _getSubType(domain):
            res = fstype.search(domain, limit=1)
            if res:
                return res
            elif not res and domain:
                return fstype.search([domain[0]], limit=1)
            return res

        subtype = _getSubType([("category", "=", "service")])
        for rec in self:
            # Fara vehicul nu e o cheltuiala de flota, deci nu are de ce sa
            # ceara un tip de serviciu. Compute-ul e stocat si ruleaza pentru
            # TOATE miscarile de stoc: fara garda asta, instalarea pe o baza
            # care are deja miscari se oprea cu "Tip cheltuiala piese
            # inexistent".
            if not rec.vehicle_id:
                rec.fleet_service_type_id = False
                continue
            if rec.refuel:
                subtype = _getSubType(
                    [
                        ("category", "=", "fuel"),
                        "|",
                        ("name", "=", "Refueling"),
                        ("name", "=", "Realimentare"),
                    ]
                )
                if not subtype:
                    raise UserError(
                        self.env._(
                            "Tip cheltuiala combustibil inexistent."
                            "Adaugati unul in Configurari/Tipuri de servicii "
                            "<Combustibil>\nEroare la %s",
                            rec.display_name,
                        )
                    )
            else:
                subtype = _getSubType(
                    [
                        ("category", "=", "parts"),
                        "|",
                        ("name", "=", "Repairing"),
                        ("name", "=", "Reparare"),
                    ]
                )
                if not subtype:
                    raise UserError(
                        self.env._(
                            "Tip cheltuiala piese inexistent."
                            "Adaugati unul in Configurari/Tipuri de servicii "
                            "<Piese>\nEroare la %s",
                            rec.display_name,
                        )
                    )
            rec.fleet_service_type_id = subtype

    def write(self, vals):
        if "vehicle_id" in vals or "refuel" in vals:
            for move in self.filtered(lambda m: m.state == "done" and m.cost_ids):
                if vals.get("vehicle_id", move.vehicle_id.id) != move.vehicle_id.id or (
                    "refuel" in vals and bool(vals["refuel"]) != move.refuel
                ):
                    raise UserError(
                        self.env._(
                            "The vehicle of done move %(move)s cannot be changed: "
                            "its cost is already booked on vehicle %(vehicle)s.",
                            move=move.display_name,
                            vehicle=move.vehicle_id.display_name,
                        )
                    )
        return super().write(vals)

    def create_vehicle_cost(self, origin=None):
        """Book the move as a vehicle cost.

        :param origin: the move this one returns; the return is booked on the
            origin's vehicle and type as a negative cost.
        """
        self.ensure_one()
        source = origin or self
        sign = -1 if origin else 1
        subtype = source.fleet_service_type_id

        if subtype.category == "contract":
            cost_type = "contract"
            model = self.env["fleet.vehicle.log.contract"]
        elif subtype.name == "Realimentare":
            cost_type = "fuel"
            model = self.env["fleet.vehicle.log.services"]
        else:
            cost_type = "services"
            model = self.env["fleet.vehicle.log.services"]

        sub_cost = {
            "vehicle_id": source.vehicle_id.id,
            "service_type_id": subtype and subtype.id,
            "product_id": self.product_id.id,
            "amount": sign * abs(self.value),
            "purchaser_id": self.create_uid.partner_id.id,
            "vendor_id": self.partner_id.id,
            "date": self.date,
            "notes": self.reference,
        }

        if cost_type == "fuel":
            sub_cost["liter"] = sign * self.quantity
            sub_cost["service_type_id"] = subtype.id
        elif cost_type == "services":
            sub_cost["service_type_id"] = subtype.id

        sub_cost["quantity"] = sign * self.quantity
        sub_cost["price_unit"] = self.price_unit
        sub_cost["stock_move_id"] = self.id

        model.create(sub_cost)

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
        for move in res:
            if (
                move.vehicle_id
                and not move.cost_ids
                and move.location_dest_id.usage in ["consume", "usage_giving"]
            ):
                move.create_vehicle_cost()
            elif (
                not move.cost_ids
                and move.origin_returned_move_id.cost_ids
                and move.location_id.usage in ["consume", "usage_giving"]
            ):
                # goods coming back from the vehicle: the cost is reversed
                move.create_vehicle_cost(origin=move.origin_returned_move_id)
        return res

    def _l10n_ro_update_fifo_split_move_vals(
        self, move, new_move_vals, fifo_item, fifo_quantity
    ):
        """Updates the move vals for a FIFO split move."""
        res = super()._l10n_ro_update_fifo_split_move_vals(
            move, new_move_vals, fifo_item, fifo_quantity
        )
        if move.vehicle_id:
            new_move_vals["vehicle_id"] = move.vehicle_id.id
        return res
