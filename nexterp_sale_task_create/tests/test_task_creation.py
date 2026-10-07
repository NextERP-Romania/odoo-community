# Copyright 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Whether confirming a sale opens the project tasks straight away.

Core always opens a task for a service sold "on task". Here that is a choice:
off by default, and when it is off the tasks are opened later, by the button.
"""

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSaleTaskCreation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create({"name": "Client"})
        cls.project = cls.env["project.project"].create(
            {"name": "Proiect", "allow_billable": True}
        )
        cls.service = cls.env["product.product"].create(
            {
                "name": "Serviciu",
                "type": "service",
                "invoice_policy": "delivery",
                "service_tracking": "task_global_project",
                "project_id": cls.project.id,
                "list_price": 100.0,
            }
        )

    def _order(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    Command.create(
                        {"product_id": self.service.id, "product_uom_qty": 1}
                    )
                ],
            }
        )
        order.onchange_company_id_task()
        return order

    def test_by_default_confirming_opens_no_task(self):
        order = self._order()
        order.action_confirm()
        self.assertFalse(order.order_line.task_id)

    def test_with_the_setting_on_confirming_opens_the_task(self):
        self.company.sale_create_taks_auto = True
        order = self._order()
        order.action_confirm()
        self.assertTrue(order.order_line.task_id)

    def test_the_order_takes_the_choice_from_its_company(self):
        self.company.sale_create_taks_auto = True
        self.assertTrue(self._order().sale_create_taks_auto)

    def test_the_choice_can_be_overridden_on_the_order(self):
        """One sale is handled differently from the rest; the company setting
        is only the default."""
        self.company.sale_create_taks_auto = True
        order = self._order()
        order.sale_create_taks_auto = False
        order.action_confirm()
        self.assertFalse(order.order_line.task_id)

    def test_the_button_opens_the_tasks_that_were_left_out(self):
        order = self._order()
        order.action_confirm()
        order.action_generate_tasks()
        self.assertTrue(order.order_line.task_id)

    def test_the_button_does_not_open_a_second_task(self):
        self.company.sale_create_taks_auto = True
        order = self._order()
        order.action_confirm()
        task = order.order_line.task_id
        order.action_generate_tasks()
        self.assertEqual(order.order_line.task_id, task)

    def test_the_setting_follows_the_company(self):
        self.assertFalse(
            self.env["res.config.settings"].create({}).sale_create_taks_auto
        )
        self.company.sale_create_taks_auto = True
        self.assertTrue(
            self.env["res.config.settings"].create({}).sale_create_taks_auto
        )
