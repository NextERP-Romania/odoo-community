# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import models


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
