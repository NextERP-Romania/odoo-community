# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _compute_tasks_ids(self):
        for order in self:
            for line in order.kit_line_ids:
                if line.task_id and not line.task_id.sale_line_id:
                    line.task_id.sale_line_id = line.sale_line_id
        return super(SaleOrder, order)._compute_tasks_ids()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _timesheet_create_task(self, project):
        """Generate task for each kit line"""
        res = super(SaleOrderLine, self)._timesheet_create_task(project)
        if self.product_id.service_tracking == "task_in_project":
            if not project:
                project = self.task_id.project_id
            for kit_line in self.kit_line_ids:
                if kit_line.product_id.service_tracking == "task_in_project":
                    if not kit_line.task_id and kit_line.sale_line_id:
                        kit_line.with_context(parent_task=res)._timesheet_create_task(
                            project
                        )
        return res
