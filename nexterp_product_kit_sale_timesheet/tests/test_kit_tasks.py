# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""A kit of services opens a task for each service in it.

Core opens one task for the line the customer sees. A kit is sold as one
line but done as several jobs, so each component that is tracked on a task
gets its own, hanging under the task of the kit.
"""

from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestKitTasks(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # `nexterp_sale_task_create`, din acelasi repo, tine generarea
        # sarcinilor la confirmare pe o setare a firmei. Fara ea nu s-ar
        # deschide nicio sarcina, nici pentru kit, nici pentru restul.
        cls.env.company.sale_create_taks_auto = True
        cls.partner = cls.env["res.partner"].create({"name": "Client"})
        cls.pricelist = cls.env["product.pricelist"].create(
            {"name": "Lista", "currency_id": cls.env.company.currency_id.id}
        )
        cls.montaj = cls._service("Montaj")
        cls.instruire = cls._service("Instruire")
        cls.piesa = cls.env["product.product"].create(
            {"name": "Piesa", "type": "consu", "list_price": 10.0}
        )
        cls.kit = cls._service("Punere in functiune")
        cls.kit.kit_product_ids = [
            Command.create({"component_product_id": cls.montaj.id, "product_qty": 1}),
            Command.create(
                {"component_product_id": cls.instruire.id, "product_qty": 1}
            ),
        ]

    @classmethod
    def _service(cls, name, tracking="task_in_project"):
        return cls.env["product.product"].create(
            {
                "name": name,
                "type": "service",
                "invoice_policy": "delivery",
                # `task_in_project` isi face singur proiectul, deci produsul
                # nu poate purta unul global.
                "service_tracking": tracking,
                "list_price": 100.0,
            }
        )

    def _order(self, product=None):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "pricelist_id": self.pricelist.id,
                "order_line": [
                    Command.create(
                        {"product_id": (product or self.kit).id, "product_uom_qty": 1}
                    )
                ],
            }
        )
        # Steagul de pe comanda nu e calculat: il pune onchange-ul din
        # `nexterp_sale_task_create` cand se alege firma.
        order.onchange_company_id_task()
        return order

    def _kit_line(self, order, product):
        return order.kit_line_ids.filtered(lambda line: line.product_id == product)

    # ------------------------------------------------------------------
    # Cate sarcini se deschid
    # ------------------------------------------------------------------
    def test_each_service_in_the_kit_gets_its_own_task(self):
        order = self._order()
        order.action_confirm()
        self.assertTrue(self._kit_line(order, self.montaj).task_id)
        self.assertTrue(self._kit_line(order, self.instruire).task_id)

    def test_the_line_the_customer_sees_still_has_its_own_task(self):
        order = self._order()
        order.action_confirm()
        self.assertTrue(order.order_line.task_id)

    def test_the_component_tasks_hang_under_the_task_of_the_kit(self):
        """Otherwise the project shows a flat list and nobody can tell which
        jobs belong to which sale."""
        order = self._order()
        order.action_confirm()
        parent = order.order_line.task_id
        for product in (self.montaj, self.instruire):
            self.assertEqual(self._kit_line(order, product).task_id.parent_id, parent)

    def test_a_component_that_is_not_tracked_opens_no_task(self):
        self.kit.kit_product_ids = [
            Command.create({"component_product_id": self.piesa.id, "product_qty": 1})
        ]
        order = self._order()
        order.action_confirm()
        self.assertFalse(self._kit_line(order, self.piesa).task_id)

    def test_a_plain_service_sold_on_its_own_behaves_as_before(self):
        order = self._order(self.montaj)
        order.action_confirm()
        self.assertTrue(order.order_line.task_id)
        self.assertFalse(order.kit_line_ids)

    def test_confirming_twice_does_not_open_a_second_task(self):
        order = self._order()
        order.action_confirm()
        task = self._kit_line(order, self.montaj).task_id
        order.order_line._timesheet_create_task(order.order_line.task_id.project_id)
        self.assertEqual(self._kit_line(order, self.montaj).task_id, task)

    # ------------------------------------------------------------------
    # Cum arata sarcina
    # ------------------------------------------------------------------
    def test_the_task_is_named_after_the_order_the_kit_and_the_service(self):
        order = self._order()
        order.action_confirm()
        task = self._kit_line(order, self.montaj).task_id
        self.assertEqual(
            task.name, f"{order.name}: {self.kit.name} - {self.montaj.name}"
        )

    def test_the_task_points_back_at_the_line_that_sold_the_kit(self):
        """That is what makes the work billable against the right line."""
        order = self._order()
        order.action_confirm()
        self.assertEqual(
            self._kit_line(order, self.montaj).task_id.sale_line_id,
            order.order_line,
        )

    def test_the_component_tasks_land_in_the_project_of_the_sale(self):
        """One project per sale, with every job of the kit inside it."""
        order = self._order()
        order.action_confirm()
        project = order.order_line.task_id.project_id
        self.assertTrue(project)
        for product in (self.montaj, self.instruire):
            self.assertEqual(self._kit_line(order, product).task_id.project_id, project)

    def test_the_task_says_which_sale_it_came_from(self):
        order = self._order()
        order.action_confirm()
        task = self._kit_line(order, self.montaj).task_id
        self.assertTrue(
            any(order.name in (m.body or "") for m in task.message_ids),
            "chatter-ul sarcinii trebuie sa trimita la comanda",
        )

    # ------------------------------------------------------------------
    # Legatura inapoi dinspre comanda
    # ------------------------------------------------------------------
    def test_a_component_task_without_a_line_is_reattached(self):
        """A task made by hand in the project has no sale line; reading the
        order's tasks is what repairs the link."""
        order = self._order()
        order.action_confirm()
        kit_line = self._kit_line(order, self.montaj)
        kit_line.task_id.sale_line_id = False
        order.invalidate_recordset(["tasks_ids"])
        order._compute_tasks_ids()
        self.assertEqual(kit_line.task_id.sale_line_id, order.order_line)

    def test_a_task_that_already_has_a_line_is_left_alone(self):
        order = self._order()
        order.action_confirm()
        kit_line = self._kit_line(order, self.montaj)
        other_order = self._order(self.montaj)
        other_order.action_confirm()
        kit_line.task_id.sale_line_id = other_order.order_line
        order._compute_tasks_ids()
        self.assertEqual(kit_line.task_id.sale_line_id, other_order.order_line)
