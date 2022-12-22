# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).

from odoo import _, models


class SaleOrderLineKit(models.Model):
    _inherit = "sale.order.line.kit"

    def _timesheet_create_task_prepare_values(self, project):
        res = super()._timesheet_create_task_prepare_values(project)
        if self.sale_line_id:
            res["sale_line_id"] = self.sale_line_id.id
            sale_line_name = self.sale_line_id.product_id.name
            res["name"] = "%s: %s - %s" % (
                self.order_id.name or "",
                sale_line_name,
                self.product_id.name,
            )
        if self.env.context.get("parent_task"):
            res["parent_id"] = self.env.context.get("parent_task").id
        return res

    def _timesheet_create_task(self, project):
        """Generate task for the given so line, and link it.
        :param project: record of project.project in which the task
        should be created
        :return task: record of the created task
        """
        values = self._timesheet_create_task_prepare_values(project)
        task = self.env["project.task"].sudo().create(values)
        self.write({"task_id": task.id})
        # post message on task
        task_msg = _(
            "This task has been created from: "
            "<a href=# data-oe-model=sale.order data-oe-id=%(sale)s>%(order)s</a>"
            " (%(product)s)"
        ) % {
            "sale": self.order_id.id,
            "order": self.order_id.name,
            "product": self.product_id.name,
        }
        task.message_post(body=task_msg)
        return task
