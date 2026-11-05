# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Fuel and parts booked against a vehicle.

A goods issue to a vehicle is a vehicle cost: refuelling goes to the fuel
log, anything else to repairs. The cost also drags along the vehicle's
non-deductible VAT share, which is what Romanian law asks for.
"""

from datetime import date

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class FleetCommon(TransactionCase):
    @classmethod
    def _vehicle(cls, **vals):
        model = cls.env["fleet.vehicle.model"].search([], limit=1)
        if not model:
            brand = cls.env["fleet.vehicle.model.brand"].create({"name": "Dacia"})
            model = cls.env["fleet.vehicle.model"].create(
                {"name": "Logan", "brand_id": brand.id}
            )
        return cls.env["fleet.vehicle"].create({"model_id": model.id, **vals})

    def _move_vals(self, vehicle, refuel=False):
        return {
            "product_id": self.product.id,
            "product_uom_qty": 10,
            "location_id": self.env.ref("stock.stock_location_stock").id,
            "location_dest_id": self.env.ref("stock.stock_location_customers").id,
            "vehicle_id": vehicle.id,
            "refuel": refuel,
        }

    def _move(self, vehicle, refuel=False):
        return self.env["stock.move"].create(self._move_vals(vehicle, refuel))


@tagged("post_install", "-at_install")
class TestVehicleServiceType(FleetCommon):
    """Which kind of cost a goods issue to a vehicle is."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vehicle = cls._vehicle()
        cls.parts_type = cls.env["fleet.service.type"].create(
            {"name": "Reparare", "category": "parts"}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Motorina", "is_storable": True}
        )

    def test_without_a_fuel_type_configured_the_move_says_so(self):
        self.env["fleet.service.type"].search([("category", "=", "fuel")]).unlink()
        move = self.env["stock.move"].new(self._move_vals(self.vehicle, refuel=True))
        with self.assertRaises(UserError) as caught:
            move._compute_fleet_service_type_id()
        self.assertIn("combustibil", str(caught.exception))

    def test_a_refuelling_is_filed_as_fuel(self):
        move = self._move(self.vehicle, refuel=True)
        self.assertEqual(move.fleet_service_type_id.category, "fuel")
        self.assertEqual(move.fleet_service_type_id.name, "Realimentare")

    def test_anything_else_is_filed_as_parts(self):
        self.assertEqual(
            self._move(self.vehicle).fleet_service_type_id, self.parts_type
        )

    def test_changing_the_move_to_a_refuelling_refiles_it(self):
        move = self._move(self.vehicle)
        move.refuel = True
        self.assertEqual(move.fleet_service_type_id.category, "fuel")

    def test_without_a_parts_type_configured_the_move_says_so(self):
        """Better a clear message than a cost filed under the wrong head --
        and the message itself has to hold together."""
        self.env["fleet.service.type"].search([("category", "=", "parts")]).unlink()
        move = self.env["stock.move"].new(self._move_vals(self.vehicle))
        with self.assertRaises(UserError) as caught:
            move._compute_fleet_service_type_id()
        self.assertIn("Piese", str(caught.exception))

    def test_the_two_romanian_categories_are_there(self):
        categories = dict(self.env["fleet.service.type"]._fields["category"].selection)
        self.assertIn("fuel", categories)
        self.assertIn("parts", categories)


@tagged("post_install", "-at_install")
class TestVehicleNonDeductible(FleetCommon):
    """The vehicle's non-deductible VAT share reaches the goods issue."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax = cls.env["account.tax"].create(
            {"name": "TVA nedeductibil", "amount": 19.0}
        )
        cls.vehicle = cls._vehicle(
            not_deductible=True,
            l10n_ro_nondeductible_percent="50",
            tax_non_deductible=cls.tax.id,
        )
        cls.env["fleet.service.type"].create({"name": "Reparare", "category": "parts"})
        cls.product = cls.env["product.product"].create(
            {"name": "Motorina", "is_storable": True}
        )

    def test_the_vehicle_carries_its_own_share(self):
        self.assertEqual(self.vehicle.l10n_ro_nondeductible_percent, "50")
        self.assertEqual(self.vehicle.tax_non_deductible, self.tax)

    def test_a_vehicle_is_fully_deductible_until_told_otherwise(self):
        other = self._vehicle()
        self.assertEqual(other.l10n_ro_nondeductible_percent, "0")
        self.assertFalse(other.not_deductible)

    def test_picking_the_vehicle_on_a_move_brings_its_share_along(self):
        move = self._move(self.vehicle)
        move._onchange_fleet_service_type_id()
        self.assertEqual(move.l10n_ro_nondeductible_tax_id, self.tax)
        self.assertEqual(move.l10n_ro_nondeductible_percent, "50")

    def test_a_deductible_vehicle_leaves_the_move_alone(self):
        move = self._move(self._vehicle())
        move._onchange_fleet_service_type_id()
        self.assertFalse(move.l10n_ro_nondeductible_tax_id)


@tagged("post_install", "-at_install")
class TestVehicleContract(FleetCommon):
    """A vehicle contract invoiced as a whole, spread over its own term."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vehicle = cls._vehicle()

    def _contract(self, **vals):
        return self.env["fleet.vehicle.log.contract"].create(
            {
                "vehicle_id": self.vehicle.id,
                "start_date": date(2026, 1, 1),
                "expiration_date": date(2026, 12, 31),
                "cost_generated": 100.0,
                **vals,
            }
        )

    def test_a_shorter_term_raises_the_monthly_amount(self):
        """The contract is worth what it is worth; shortening it only packs
        the same money into fewer months."""
        form = Form(self._contract())
        form.expiration_date = date(2026, 6, 30)
        self.assertAlmostEqual(form.cost_generated, 200.0)

    def test_a_longer_term_lowers_it(self):
        form = Form(self._contract())
        form.expiration_date = date(2027, 12, 31)
        self.assertAlmostEqual(form.cost_generated, 50.0)

    def test_the_contract_knows_whose_vehicle_it_is(self):
        owner = self.env["res.partner"].create({"name": "Proprietar"})
        self.vehicle.owner_id = owner
        self.assertEqual(self._contract().owner_id, owner)


@tagged("post_install", "-at_install")
class TestVehicleCostFlow(FleetCommon):
    """Goods issued to a vehicle become its cost and stay tied to the move."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vehicle = cls._vehicle()
        cls.other_vehicle = cls._vehicle()
        cls.env["fleet.service.type"].create({"name": "Reparare", "category": "parts"})
        cls.product = cls.env["product.product"].create(
            {"name": "Filtru ulei", "is_storable": True, "standard_price": 5.0}
        )
        cls.stock = cls.env.ref("stock.stock_location_stock")
        cls.consume = cls.env["stock.location"].create(
            {
                "name": "Consum flota",
                "usage": "consume",
                "location_id": cls.stock.location_id.id,
            }
        )
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.stock, 10)

    def _done_move(self, src, dest, qty, **vals):
        move = self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom_qty": qty,
                "location_id": src.id,
                "location_dest_id": dest.id,
                **vals,
            }
        )
        move._action_confirm()
        move._action_assign()
        move.quantity = qty
        move.picked = True
        move._action_done()
        self.assertEqual(move.state, "done")
        return move

    def _issue(self, qty=4):
        return self._done_move(
            self.stock, self.consume, qty, vehicle_id=self.vehicle.id
        )

    def test_flow_issuing_goods_to_a_vehicle_books_its_cost(self):
        move = self._issue()
        cost = move.cost_ids
        self.assertEqual(len(cost), 1)
        self.assertEqual(cost.vehicle_id, self.vehicle)
        self.assertEqual(cost.product_id, self.product)
        self.assertEqual(cost.quantity, 4)
        self.assertEqual(cost.amount, abs(move.value))
        self.assertEqual(cost.service_type_id.category, "parts")

    def test_flow_returning_the_goods_reverses_the_cost(self):
        move = self._issue()
        back = self._done_move(
            self.consume, self.stock, 4, origin_returned_move_id=move.id
        )
        self.assertEqual(back.cost_ids.vehicle_id, self.vehicle)
        self.assertEqual(back.cost_ids.quantity, -4)
        self.assertEqual(back.cost_ids.amount, -abs(back.value))
        self.assertEqual(sum((move.cost_ids | back.cost_ids).mapped("quantity")), 0)

    def test_the_vehicle_of_a_booked_move_cannot_be_changed(self):
        move = self._issue()
        with self.assertRaises(UserError):
            move.vehicle_id = self.other_vehicle
        with self.assertRaises(UserError):
            move.refuel = True
        self.assertEqual(move.vehicle_id, self.vehicle)
        self.assertEqual(move.cost_ids.vehicle_id, self.vehicle)

    def test_a_cost_booked_from_a_done_move_follows_it(self):
        move = self._issue()
        cost = move.cost_ids
        amount = cost.amount
        with self.assertRaises(UserError):
            cost.amount = 1.0
        with self.assertRaises(UserError):
            cost.vehicle_id = self.other_vehicle
        with self.assertRaises(UserError):
            cost.unlink()
        self.assertEqual(cost.amount, amount)
        cost.notes = "Schimb filtru la 120.000 km"
        self.assertEqual(cost.notes, "Schimb filtru la 120.000 km")

    def test_a_move_not_done_yet_keeps_its_vehicle_editable(self):
        move = self._move(self.vehicle)
        move.vehicle_id = self.other_vehicle
        self.assertEqual(move.vehicle_id, self.other_vehicle)
        self.assertFalse(move.cost_ids)

    def test_a_cost_typed_by_hand_stays_editable(self):
        cost = self.env["fleet.vehicle.log.services"].create(
            {
                "vehicle_id": self.vehicle.id,
                "service_type_id": self.env["fleet.service.type"]
                .search([("category", "=", "parts")], limit=1)
                .id,
                "amount": 50.0,
            }
        )
        cost.amount = 60.0
        cost.unlink()
        self.assertFalse(cost.exists())


@tagged("post_install", "-at_install")
class TestVehicleCostFromBill(AccountTestInvoicingCommon):
    """A vendor bill line on a vehicle is a vehicle cost while the bill is."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref("fleet.fleet_group_manager")
        brand = cls.env["fleet.vehicle.model.brand"].create({"name": "Dacia"})
        model = cls.env["fleet.vehicle.model"].create(
            {"name": "Logan", "brand_id": brand.id}
        )
        cls.vehicle = cls.env["fleet.vehicle"].create({"model_id": model.id})

    def _bill(self):
        bill = self.init_invoice("in_invoice", amounts=[100.0], post=False)
        bill.invoice_line_ids.vehicle_id = self.vehicle
        bill.action_post()
        return bill

    def test_posting_the_bill_books_the_vehicle_cost(self):
        bill = self._bill()
        services = bill.invoice_line_ids.vehicle_log_service_ids
        self.assertEqual(len(services), 1)
        self.assertEqual(services.vehicle_id, self.vehicle)

    def test_cancelling_the_bill_drops_the_vehicle_cost(self):
        bill = self._bill()
        services = bill.invoice_line_ids.vehicle_log_service_ids
        bill.button_draft()
        bill.button_cancel()
        self.assertEqual(bill.state, "cancel")
        self.assertFalse(services.exists())

    def test_a_bill_posted_again_books_the_cost_again(self):
        bill = self._bill()
        bill.button_draft()
        bill.button_cancel()
        bill.button_draft()
        bill.action_post()
        self.assertEqual(len(bill.invoice_line_ids.vehicle_log_service_ids), 1)
