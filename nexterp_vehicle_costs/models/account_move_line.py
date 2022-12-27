# Copyright (C) 2014 Forest AND Biomass Romania SA
# Copyright (C) 2019 OdooERP Romania SRL
# Copyright (C) 2021 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicle")
    refuel = fields.Boolean()
    cost_ids = fields.One2many(
        "fleet.vehicle.log.report", "move_line_id", string="Vehicle Costs"
    )
    veh_service_cost_ids = fields.One2many(
        "fleet.vehicle.log.services", "move_line_id", string="Vehicle Service Costs"
    )
    veh_contract_cost_ids = fields.One2many(
        "fleet.vehicle.log.contract", "move_line_id", string="Vehicle Contract Costs"
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
        elif self.product_id.vehicle_contract:
            subtype = _getSubType(
                [
                    ("category", "=", "contract"),
                    "|",
                    ("name", "=", "Taxes"),
                    ("name", "=", "Taxe"),
                ]
            )
            cost_type = "contract"
            model = self.env["fleet.vehicle.log.contract"]
            if not subtype:
                raise UserError(
                    _(
                        "Tip cheltuiala contract inexistent. "
                        "Adaugati unul in Configurari/Tipuri de servicii "
                        "<Contract>\nEroare la %s"
                    )
                    % self.name
                )
        else:
            subtype = _getSubType(
                [
                    ("category", "=", "service"),
                    "|",
                    ("name", "=", "Repairing"),
                    ("name", "=", "Reparare"),
                ]
            )
            cost_type = "services"
            model = self.env["fleet.vehicle.log.services"]
            if not subtype:
                raise UserError(
                    _(
                        "Tip cheltuiala servicii inexistent. "
                        "Adaugati unul in Configurari/Tipuri de servicii "
                        "<Service>\nEroare la %s"
                    )
                    % self.name
                )
        sub_cost = {
            "vehicle_id": self.vehicle_id.id,
            "product_id": self.product_id.id,
            "amount": (-1) * self.price_subtotal
            if self.move_id.move_type == "in_refund"
            else self.price_subtotal,
            "purchaser_id": self.create_uid.partner_id.id,
            "date": self.move_id.invoice_date,
            "notes": self.name,
            "move_line_id": self.id,
        }
        if cost_type == "fuel":
            sub_cost["liter"] = (
                (-1) * self.quantity
                if self.move_id.move_type == "in_refund"
                else self.quantity
            )
            sub_cost["price_unit"] = self.price_unit
            sub_cost["service_type_id"] = subtype and subtype.id
            sub_cost["vendor_id"] = self.partner_id.id
        elif cost_type == "services":
            sub_cost["quantity"] = (
                (-1) * self.quantity
                if self.move_id.move_type == "in_refund"
                else self.quantity
            )
            sub_cost["price_unit"] = self.price_unit
            sub_cost["inv_ref"] = self.move_id.name
            sub_cost["service_type_id"] = subtype and subtype.id
            sub_cost["vendor_id"] = self.partner_id.id
        elif cost_type == "contract":
            sub_cost.update(
                {
                    "start_date": fields.Date.from_string(self.move_id.invoice_date),
                    "expiration_date": fields.Date.from_string(
                        self.move_id.invoice_date
                    )
                    + relativedelta(years=1),
                    "cost_subtype_id": subtype and subtype.id,
                    "insurer_id": self.partner_id.id,
                    "ins_ref": self.move_id.name,
                    "state": "open",
                    "amount": 0.00,
                    "cost_generated": round((-1) * self.price_subtotal / 12, 2)
                    if self.move_id.move_type == "in_refund"
                    else round(self.price_subtotal / 12, 2),
                    "cost_frequency": "monthly",
                }
            )
        model.create(sub_cost)

    def cancel_vehicle_cost(self):
        for s in self.cost_ids:
            s.source.unlink()
