# Copyright (C) 2014 Forest AND Biomass Romania SA
# Copyright (C) 2019 OdooERP Romania SRL
# Copyright (C) 2021 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import _, fields, models
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = "stock.move"

    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        copy=False,
        states={"done": [("readonly", True)], "cancel": [("readonly", True)]},
    )
    refuel = fields.Boolean(copy=False)
    cost_ids = fields.One2many(
        "fleet.vehicle.log.services", "stock_move_id", string="Vehicle Costs"
    )

    def create_vehicle_cost(self):
        self.ensure_one()

        fstype = self.env["fleet.service.type"]

        def _getSubType(domain):
            res = fstype.search(domain, limit=1)
            if res:
                return res
            elif not res and domain:
                return fstype.search([domain[0]], limit=1)
            return res

        subtype = _getSubType([("category", "=", "service")])
        cost_type = "services"
        model = self.env["fleet.vehicle.log.services"]

        if self.refuel:
            subtype = _getSubType(
                [
                    ("category", "=", "fuel"),
                    "|",
                    ("name", "=", "Refueling"),
                    ("name", "=", "Realimentare"),
                ]
            )
            cost_type = "fuel"
            model = self.env["fleet.vehicle.log.services"]
            if not subtype:
                raise UserError(
                    _(
                        "Tip cheltuiala combustibil inexistent."
                        "Adaugati unul in Configurari/Tipuri de servicii "
                        "<Combustibil>\nEroare la %s"
                    )
                    % self.name
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
            cost_type = "parts"
            model = self.env["fleet.vehicle.log.services"]
            if not subtype:
                raise UserError(
                    _(
                        "Tip cheltuiala piese inexistent."
                        "Adaugati unul in Configurari/Tipuri de servicii "
                        "<Piese>\nEroare la %s"
                    )
                    % self.name
                )

        for svl in self.stock_valuation_layer_ids:
            sub_cost = {
                "vehicle_id": self.vehicle_id.id,
                "service_type_id": subtype and subtype.id,
                "product_id": svl.product_id.id,
                "amount": -svl.value,
                "purchaser_id": self.create_uid.partner_id.id,
                "vendor_id": self.partner_id.id,
                "date": self.date,
                "notes": self.name,
            }
            if cost_type == "fuel":
                sub_cost["liter"] = -svl.quantity

            sub_cost["quantity"] = -svl.quantity
            sub_cost["price_unit"] = svl.unit_cost
            sub_cost["stock_move_id"] = self.id

            model.create(sub_cost)

    def cancel_vehicle_cost(self):
        for s in self.cost_ids:
            s.unlink()

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            if move.vehicle_id and not move.cost_ids:
                move.create_vehicle_cost()
        return res

    def action_cancel(self):
        res = super(StockMove, self).action_cancel()
        for move in self:
            if move.vehicle_id and move.cost_ids:
                move.cancel_vehicle_cost()
        return res

    def _account_entry_move(self, qty, description, svl_id, cost):
        """Accounting Valuation Entries for nondeductible vehicle"""
        if (
            self.l10n_ro_nondeductible_usage
            and self.vehicle_id
            and self.vehicle_id.not_deductible
        ):
            tax_ids = self.product_id.supplier_taxes_id.filtered(
                lambda tax: tax.company_id == self.company_id
            )
            if tax_ids and tax_ids.mapped("l10n_ro_nondeductible_tax_id"):
                self.l10n_ro_nondeductible_tax_id = tax_ids.mapped(
                    "l10n_ro_nondeductible_tax_id"
                )[0]
            if self.vehicle_id.tax_non_deductible:
                self.l10n_ro_nondeductible_tax_id = self.vehicle_id.tax_non_deductible
        return super()._account_entry_move(qty, description, svl_id, cost)
