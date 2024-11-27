# Copyright (C) 2014 Forest AND Biomass Romania SA
# Copyright (C) 2019 OdooERP Romania SRL
# Copyright (C) 2024 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).


from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    fleet_service_type_id = fields.Many2one(
        "fleet.service.type", string="Vehicle Service Type",  domain="[('category','not in',('contract'))]"
    )

    def _prepare_fleet_log_service(self):
        res = super()._prepare_fleet_log_service()
        if self.fleet_service_type_id:
            res.update(
                {
                    "service_type_id": self.fleet_service_type_id.id,
                    "product_id": self.product_id.id,
                    "quantity": self.quantity,
                    "price_unit": self.price_unit,
                    "move_line_id": self.id,
                }
            )
            
        return res

    def _compute_need_vehicle(self):
        super()._compute_need_vehicle()
        for s in self:
            if s.fleet_service_type_id:
                s.need_vehicle = True

    def cancel_vehicle_cost(self):
        for s in self.cost_ids:
            s.source.unlink()
