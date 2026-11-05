# Copyright (C) 2014 Forest AND Biomass Romania SA
# Copyright (C) 2019 OdooERP Romania SRL
# Copyright (C) 2021 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

_FUEL = "fuel"
_PARTS = "parts"


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    owner_id = fields.Many2one("res.partner", index=True)
    not_deductible = fields.Boolean()
    # non_deductible_percent = fields.Float()
    l10n_ro_nondeductible_percent = fields.Selection(
        [("0", "Deductible"), ("50", "50% Nondeductible"), ("100", "Nondeductible")],
        string="Romania - Non Deductible Percent",
        default="0",
    )
    tax_non_deductible = fields.Many2one("account.tax", "Tax NonDeductible")

    def return_action_to_open(self):
        """This opens the xml view specified in xml_id for the current vehicle"""
        self.ensure_one()
        xml_id = self.env.context.get("xml_id")
        if xml_id:
            groupby = False
            if xml_id == "fleet_vehicle_log_services_action":
                groupby = "category_type"
            res = self.env["ir.actions.act_window"]._for_xml_id(f"fleet.{xml_id}")
            res.update(
                context=dict(
                    self.env.context, default_vehicle_id=self.id, group_by=groupby
                ),
                domain=[("vehicle_id", "=", self.id)],
            )
            return res
        return False


class FleetServiceType(models.Model):
    _inherit = "fleet.service.type"

    category = fields.Selection(
        selection_add=[(_FUEL, "Combustibil"), (_PARTS, "Parts")],
        # on uninstall the types (and the costs filed under them) are kept as
        # plain services instead of being deleted
        ondelete={
            _FUEL: lambda recs: recs.write({"category": "service"}),
            _PARTS: lambda recs: recs.write({"category": "service"}),
        },
    )


class FleetCostFromStockMixin(models.AbstractModel):
    """A cost booked from a done stock move follows the move: it can only be
    corrected by returning the goods, not edited or deleted by hand."""

    _name = "nexterp.fleet.cost.stock.mixin"
    _description = "Vehicle cost booked from a stock move"

    _STOCK_LOCKED_FIELDS = {
        "amount",
        "vehicle_id",
        "stock_move_id",
        "product_id",
        "quantity",
        "price_unit",
    }

    def _check_stock_move_lock(self):
        if any(cost.stock_move_id.state == "done" for cost in self):
            raise UserError(
                self.env._(
                    "This vehicle cost was booked from a done stock move and "
                    "follows it: return the goods to correct it."
                )
            )

    def write(self, vals):
        if self._STOCK_LOCKED_FIELDS.intersection(vals):
            self._check_stock_move_lock()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_done_stock_move(self):
        self._check_stock_move_lock()


class FleetVehicleLogServices(models.Model):
    _name = "fleet.vehicle.log.services"
    _inherit = ["fleet.vehicle.log.services", "nexterp.fleet.cost.stock.mixin"]

    owner_id = fields.Many2one(related="vehicle_id.owner_id", store=True)
    product_id = fields.Many2one("product.product")
    quantity = fields.Float()
    liter = fields.Float("Liters")
    price_unit = fields.Float()
    move_line_id = fields.Many2one("account.move.line")
    stock_move_id = fields.Many2one("stock.move")
    category_type = fields.Selection(related="service_type_id.category", store=True)


class FleetVehicleLogContract(models.Model):
    _name = "fleet.vehicle.log.contract"
    _inherit = ["fleet.vehicle.log.contract", "nexterp.fleet.cost.stock.mixin"]

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
