# Copyright 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""The eTransport rules ANAF checks before it hands out a UIT.

Everything here is a rule from the Schematron: which operation scope goes
with which operation type, which country the other party may be in, and what
a line of goods has to carry. Catching them in Odoo is the difference between
a clear message and a rejection from ANAF.
"""

from psycopg2 import IntegrityError

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from odoo.addons.l10n_ro_edi_stock_extension.models.etransport_constants import (
    is_incoming,
    is_national,
    is_outgoing,
    needs_goods_full_data,
)


@tagged("post_install", "-at_install")
class TestEtransportOperationTypes(TransactionCase):
    """What kind of movement an operation code stands for."""

    def test_the_incoming_codes_are_read_as_incoming(self):
        for code in ("10", "12", "14", "40", "60"):
            self.assertTrue(is_incoming(code), code)
            self.assertFalse(is_outgoing(code), code)

    def test_the_outgoing_codes_are_read_as_outgoing(self):
        for code in ("20", "22", "24", "50", "70"):
            self.assertTrue(is_outgoing(code), code)
            self.assertFalse(is_incoming(code), code)

    def test_thirty_is_the_national_transport(self):
        self.assertTrue(is_national("30"))
        self.assertFalse(is_incoming("30"))
        self.assertFalse(is_outgoing("30"))

    def test_the_storage_flows_need_no_goods_detail(self):
        """60 and 70 move goods that are not being sold, so the tariff code,
        the net weight and the value are not asked for."""
        self.assertFalse(needs_goods_full_data("60"))
        self.assertFalse(needs_goods_full_data("70"))

    def test_every_other_operation_needs_the_full_goods_detail(self):
        for code in ("10", "12", "14", "20", "22", "24", "30", "40", "50"):
            self.assertTrue(needs_goods_full_data(code), code)

    def test_an_unknown_code_belongs_to_no_group(self):
        self.assertFalse(is_incoming("99"))
        self.assertFalse(is_outgoing("99"))
        self.assertFalse(is_national("99"))


@tagged("post_install", "-at_install")
class TestEtransportDocumentLines(TransactionCase):
    """The accompanying documents listed on a notification."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Picking = cls.env["stock.picking"]
        picking_type = cls.env["stock.picking.type"].search(
            [("code", "=", "outgoing")], limit=1
        )
        cls.picking = cls.env["stock.picking"].create(
            {
                "picking_type_id": picking_type.id,
                "location_id": picking_type.default_location_src_id.id,
                "location_dest_id": cls.env.ref("stock.stock_location_customers").id,
            }
        )

    def _line(self, **vals):
        return self.env["l10n.ro.edi.stock.document.line"].create(
            {
                "picking_id": self.picking.id,
                "document_type": "20",
                "document_date": "2026-03-15",
                **vals,
            }
        )

    def _errors(self):
        return self.Picking._l10n_ro_edi_stock_validate_doc_lines(self.picking)

    def test_a_complete_line_passes(self):
        self._line()
        self.assertFalse(self._errors())

    def test_a_line_cannot_be_saved_without_a_type_or_a_date(self):
        """ANAF wants both for every accompanying document, so they are
        required outright rather than only reported."""
        for vals in ({"document_type": False}, {"document_date": False}):
            with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
                with self.cr.savepoint():
                    self._line(**vals)

    def test_other_without_a_remark_is_reported(self):
        """BR-026: 'Other' says nothing on its own, so the remark is what
        names the document."""
        self._line(document_type="9999")
        self.assertTrue(self._errors())

    def test_other_with_a_remark_passes(self):
        self._line(document_type="9999", remarks="Aviz intern 123")
        self.assertFalse(self._errors())

    def test_a_notification_without_any_line_has_nothing_to_report(self):
        self.assertFalse(self._errors())


@tagged("post_install", "-at_install")
class TestForeignCounterparty(TransactionCase):
    """The base module's "warehouse must be in Romania" check fires on the
    other party too, which would make every intra-EU notification impossible.
    It is dropped there and kept on our own side."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Picking = cls.env["stock.picking"]
        cls.outgoing_type = cls.env["stock.picking.type"].search(
            [("code", "=", "outgoing")], limit=1
        )
        cls.incoming_type = cls.env["stock.picking.type"].search(
            [("code", "=", "incoming")], limit=1
        )

    def _data(self, op_type, picking_type, side):
        return {
            "l10n_ro_edi_stock_operation_type": op_type,
            "picking_type_id": picking_type,
            f"l10n_ro_edi_stock_{side}_loc_type": "location",
        }

    def _spurious(self, side):
        return self.Picking._l10n_ro_edi_stock_base_foreign_location_error(side)

    def test_the_error_is_dropped_on_the_receiving_side_of_an_export(self):
        errors = [self._spurious("end"), "altceva"]
        kept = self.Picking._l10n_ro_edi_stock_drop_foreign_counterparty_error(
            errors, self._data("20", self.outgoing_type, "end")
        )
        self.assertEqual(kept, ["altceva"])

    def test_the_error_is_dropped_on_the_sending_side_of_an_import(self):
        errors = [self._spurious("start")]
        kept = self.Picking._l10n_ro_edi_stock_drop_foreign_counterparty_error(
            errors, self._data("10", self.incoming_type, "start")
        )
        self.assertEqual(kept, [])

    def test_the_error_is_kept_on_our_own_side(self):
        """Our warehouse really does have to be in Romania."""
        errors = [self._spurious("start")]
        kept = self.Picking._l10n_ro_edi_stock_drop_foreign_counterparty_error(
            errors, self._data("20", self.outgoing_type, "end")
        )
        self.assertEqual(kept, errors)

    def test_the_error_is_kept_for_a_national_transport(self):
        errors = [self._spurious("end")]
        kept = self.Picking._l10n_ro_edi_stock_drop_foreign_counterparty_error(
            errors, self._data("30", self.outgoing_type, "end")
        )
        self.assertEqual(kept, errors)

    def test_an_address_typed_by_hand_is_left_alone(self):
        data = self._data("20", self.outgoing_type, "end")
        data["l10n_ro_edi_stock_end_loc_type"] = "bcpi"
        errors = [self._spurious("end")]
        self.assertEqual(
            self.Picking._l10n_ro_edi_stock_drop_foreign_counterparty_error(
                errors, data
            ),
            errors,
        )
