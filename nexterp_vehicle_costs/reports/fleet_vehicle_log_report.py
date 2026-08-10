# Part of Odoo. See LICENSE file for full copyright and licensing details.
from psycopg2 import sql

from odoo import fields, models, tools


class FleetLogReport(models.Model):
    _name = "fleet.vehicle.log.report"
    _description = "Fleet Cost Unified"
    _auto = False
    _order = "date desc"

    active = fields.Boolean()
    amount = fields.Monetary("Cost")
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
    date = fields.Date(help="Date when the cost has been executed")
    product_id = fields.Many2one("product.product")
    purchaser_id = fields.Many2one("res.partner", string="Driver")
    quantity = fields.Float()
    state = fields.Selection(
        [
            ("futur", "Incoming"),
            ("open", "In Progress"),
            ("expired", "Expired"),
            ("closed", "Closed"),
            ("todo", "To Do"),
            ("running", "Running"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="Stage",
    )

    price_unit = fields.Float("")
    stock_move_id = fields.Many2one("stock.move")
    move_line_id = fields.Many2one("account.move.line")
    company_id = fields.Many2one("res.company")
    vehicle_id = fields.Many2one("fleet.vehicle")
    cost_type = fields.Selection(
        selection=[
            ("contract", "Contract"),
            ("service", "Service"),
            ("fuel", "Fuel"),
        ],
    )
    cost_subtype_id = fields.Many2one("fleet.service.type")
    source = fields.Reference(
        [
            ("fleet.vehicle.log.service", "Service Log"),
            ("fleet.vehicle.log.contract", "Contract Log"),
        ],
        string="Source Data",
    )

    def init(self):
        query = """
        SELECT
            5000000 + vls.id as id,
            vls.active as active,
            vls.amount as amount,
            vls.date as date,
            vls.product_id as product_id,
            vls.purchaser_id as purchaser_id,
            (vls.quantity + vls.liter) as quantity,
            vls.state as state,
            vls.price_unit as price_unit,
            vls.move_line_id as move_line_id,
            vls.stock_move_id as stock_move_id,
            vls.company_id as company_id,
            vls.vehicle_id as vehicle_id,
            fst.category as cost_type,
            fst.id as cost_subtype_id,
            concat('fleet.vehicle.log.service',',',vls.id) as source
        FROM
            fleet_vehicle_log_services vls
        LEFT JOIN
            fleet_service_type fst on (fst.id=vls.service_type_id)
UNION ALL
        SELECT
            vlc.id as id,
            vlc.active as active,
            vlc.amount as amount,
            vlc.date as date,
            vlc.product_id as product_id,
            vlc.purchaser_id as purchaser_id,
            vlc.quantity as quantity,
            vlc.state as state,
            vlc.price_unit as price_unit,
            vlc.move_line_id as move_line_id,
            vlc.stock_move_id as stock_move_id,
            vlc.company_id as company_id,
            vlc.vehicle_id as vehicle_id,
            fst.category as cost_type,
            fst.id as cost_subtype_id,
            concat('fleet.vehicle.log.contract',',',vlc.id) as source
        FROM
            fleet_vehicle_log_contract vlc
        LEFT JOIN
            fleet_service_type fst on (fst.id=vlc.cost_subtype_id)
        """
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            sql.SQL("""CREATE or REPLACE VIEW {} as ({})""").format(
                sql.Identifier(self._table), sql.SQL(query)
            )
        )
