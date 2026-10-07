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
