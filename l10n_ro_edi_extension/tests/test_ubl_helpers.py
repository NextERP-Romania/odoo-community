# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Walking the children of a UBL node, whether Odoo emitted one or a list."""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestUblHelpers(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ubl = cls.env["account.edi.xml.ubl_ro"]

    # ------------------------------------------------------------------
    # Copiii unui nod
    # ------------------------------------------------------------------
    def test_a_single_child_is_walked_like_a_list_of_one(self):
        parent = {"cac:Line": {"id": 1}}
        self.assertEqual(
            list(self.ubl._ro_iter_children(parent, "cac:Line")), [{"id": 1}]
        )

    def test_several_children_come_back_in_order(self):
        parent = {"cac:Line": [{"id": 1}, {"id": 2}]}
        self.assertEqual(
            [c["id"] for c in self.ubl._ro_iter_children(parent, "cac:Line")], [1, 2]
        )

    def test_a_missing_child_yields_nothing(self):
        self.assertEqual(list(self.ubl._ro_iter_children({}, "cac:Line")), [])
        self.assertEqual(list(self.ubl._ro_iter_children(None, "cac:Line")), [])

    def test_text_in_place_of_a_child_is_skipped(self):
        parent = {"cac:Line": ["nu e nod", {"id": 1}]}
        self.assertEqual(
            [c["id"] for c in self.ubl._ro_iter_children(parent, "cac:Line")], [1]
        )
