# Copyright (C) 2014 Forest AND Biomass Romania SA
# Copyright (C) 2019 OdooERP Romania SRL
# Copyright (C) 2021 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

_FUEL = "fuel"
_PARTS = "parts"


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    owner_id = fields.Many2one("res.partner", "Vehicle Owner", index=True)
    not_deductible = fields.Boolean()
    tax_non_deductible = fields.Many2one("account.tax", "Tax NonDeductible")


class FleetServiceType(models.Model):
    _inherit = "fleet.service.type"

    category = fields.Selection(
        selection_add=[(_FUEL, _("Combustibil")), (_PARTS, _("Parts"))],
        ondelete={_FUEL: "cascade", _PARTS: "cascade"},
    )


class FleetVehicleLogServices(models.Model):
    _inherit = "fleet.vehicle.log.services"

    owner_id = fields.Many2one(related="vehicle_id.owner_id", store=True)
    product_id = fields.Many2one("product.product")
    quantity = fields.Float()
    liter = fields.Float("Liters")
    price_unit = fields.Float()
    move_line_id = fields.Many2one("account.move.line")
    stock_move_id = fields.Many2one("stock.move")


class FleetVehicleLogContract(models.Model):
    _inherit = "fleet.vehicle.log.contract"

    owner_id = fields.Many2one(related="vehicle_id.owner_id", store=True)
    product_id = fields.Many2one("product.product")
    quantity = fields.Float()
    price_unit = fields.Float()
    move_line_id = fields.Many2one("account.move.line")
    stock_move_id = fields.Many2one("stock.move")
    purchaser_id = fields.Many2one(store=True)

    @api.onchange("expiration_date")
    def _onchange_expiration_date(self):
        if self.move_line_id:
            amount = self.move_line_id.price_subtotal
        else:
            r = relativedelta(self._origin.expiration_date, self.start_date)
            months = r.months + 12 * r.years + 1
            amount = self.cost_generated * months
        r = relativedelta(self.expiration_date, self.start_date)
        months = r.months + 12 * r.years + 1
        self.cost_generated = amount / months
