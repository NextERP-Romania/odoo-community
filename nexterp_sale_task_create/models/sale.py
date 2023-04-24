# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    sale_create_taks_auto = fields.Boolean(string="Auto Create Sale Tasks")

    @api.onchange("company_id")
    def onchange_company_id_task(self):
        """
        Trigger the change of sale_create_taks_auto.
        """
        self.sale_create_taks_auto = self.company_id.sale_create_taks_auto

    def action_generate_tasks(self):
        for order in self:
            for line in order.order_line:
                if not line.task_id:
                    line.sudo().with_company(
                        order.company_id
                    )._timesheet_service_generation()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_service_generation(self):
        so_line_create_tasks = self.filtered(
            lambda sol: sol.order_id.sale_create_taks_auto
        )
        return super(
            SaleOrderLine, so_line_create_tasks
        )._timesheet_service_generation()
