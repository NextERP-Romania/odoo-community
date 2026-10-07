# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Keeping the invoice XML inside the lengths ANAF accepts.

The RO CIUS caps almost every text field (BR-RO-L100/L200/L300...). A field
one character over is not rejected by Odoo, by the XSD or by any local check
-- only by ANAF, after the invoice has been sent. So the cutting happens
here, in one pass over the finished document.
"""

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestUblLengths(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ubl = cls.env["account.edi.xml.ubl_ro"]

    # ------------------------------------------------------------------
    # Taierea unui text
    # ------------------------------------------------------------------
    def test_a_text_over_the_limit_is_cut_to_it(self):
        self.assertEqual(len(self.ubl._ro_truncate("x" * 500, 200)), 200)

    def test_a_text_under_the_limit_is_left_whole(self):
        self.assertEqual(self.ubl._ro_truncate("Factura", 200), "Factura")

    def test_nothing_stays_nothing(self):
        """An empty field must not become the string "False" in the XML."""
        self.assertFalse(self.ubl._ro_truncate("", 200))
        self.assertFalse(self.ubl._ro_truncate(False, 200))

    def test_a_number_is_cut_as_text(self):
        self.assertEqual(self.ubl._ro_truncate(1234567, 3), "123")

    # ------------------------------------------------------------------
    # Spargerea notei in bucati
    # ------------------------------------------------------------------
    def test_a_short_note_stays_one_piece(self):
        self.assertEqual(self.ubl.split_string("Nota scurta", 300), ["Nota scurta"])

    def test_a_long_note_is_split_into_pieces_within_the_limit(self):
        pieces = self.ubl.split_string("a" * 750, 300)
        self.assertEqual(len(pieces), 3)
        self.assertTrue(all(len(p) <= 300 for p in pieces))
        self.assertEqual("".join(pieces), "a" * 750)

    def test_the_pieces_stay_under_the_limit_in_bytes_too(self):
        """Some validators count bytes, and Romanian diacritics take two in
        UTF-8: a piece of 300 characters would be 600 bytes."""
        pieces = self.ubl.split_string("ă" * 400, 300)
        self.assertTrue(all(len(p.encode("utf-8")) <= 300 for p in pieces))

    def test_nothing_splits_into_nothing(self):
        self.assertEqual(self.ubl.split_string("", 300), [])

    def test_a_note_of_only_spaces_yields_no_piece(self):
        self.assertEqual(self.ubl.split_string("     ", 300), [])

    def test_the_split_does_not_lose_the_words(self):
        text = "Plata se face in 30 de zile. " * 20
        pieces = self.ubl.split_string(text, 300)
        self.assertIn("Plata se face in 30 de zile.", " ".join(pieces))

    # ------------------------------------------------------------------
    # Plimbarea pe arborele documentului
    # ------------------------------------------------------------------
    def test_a_text_node_deep_in_the_tree_is_cut(self):
        document = {"cac:OrderReference": {"cbc:ID": {"_text": "x" * 400}}}
        self.ubl._ro_apply_path(document, ("cac:OrderReference", "cbc:ID"), 200)
        self.assertEqual(len(document["cac:OrderReference"]["cbc:ID"]["_text"]), 200)

    def test_an_attribute_held_as_plain_text_is_cut_too(self):
        document = {"cac:OrderReference": {"cbc:ID": "x" * 400}}
        self.ubl._ro_apply_path(document, ("cac:OrderReference", "cbc:ID"), 200)
        self.assertEqual(len(document["cac:OrderReference"]["cbc:ID"]), 200)

    def test_every_item_of_a_repeated_node_is_cut(self):
        document = {"cac:Lines": [{"cbc:ID": {"_text": "x" * 400}} for _ in range(3)]}
        self.ubl._ro_apply_path(document, ("cac:Lines", "cbc:ID"), 200)
        for line in document["cac:Lines"]:
            self.assertEqual(len(line["cbc:ID"]["_text"]), 200)

    def test_a_path_that_is_not_there_is_not_an_error(self):
        """Odoo does not emit every optional node; walking has to survive
        that."""
        document = {"cbc:ID": {"_text": "F-1"}}
        self.ubl._ro_apply_path(document, ("cac:OrderReference", "cbc:ID"), 200)
        self.assertEqual(document, {"cbc:ID": {"_text": "F-1"}})

    def test_an_empty_node_is_left_alone(self):
        document = {"cac:OrderReference": None}
        self.ubl._ro_apply_path(document, ("cac:OrderReference", "cbc:ID"), 200)
        self.assertIsNone(document["cac:OrderReference"])

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

    # ------------------------------------------------------------------
    # Trecerea finala peste tot documentul
    # ------------------------------------------------------------------
    def test_the_final_pass_cuts_the_document_fields(self):
        document = {
            "cbc:ID": {"_text": "x" * 400},
            "cbc:AccountingCost": {"_text": "y" * 400},
            "cac:PaymentTerms": {"cbc:Note": {"_text": "z" * 400}},
        }
        self.ubl._ro_apply_length_limits(document)
        self.assertEqual(len(document["cbc:ID"]["_text"]), 200)
        self.assertEqual(len(document["cbc:AccountingCost"]["_text"]), 100)
        self.assertEqual(len(document["cac:PaymentTerms"]["cbc:Note"]["_text"]), 300)

    def test_the_final_pass_cuts_both_parties(self):
        def party(name):
            return {
                "cac:Party": {
                    "cac:PartyLegalEntity": {"cbc:RegistrationName": {"_text": name}},
                    "cac:PostalAddress": {
                        "cbc:CityName": {"_text": "c" * 200},
                        "cbc:PostalZone": {"_text": "9" * 60},
                    },
                }
            }

        document = {
            "cac:AccountingSupplierParty": party("f" * 400),
            "cac:AccountingCustomerParty": party("c" * 400),
        }
        self.ubl._ro_apply_length_limits(document)
        for key in ("cac:AccountingSupplierParty", "cac:AccountingCustomerParty"):
            party_node = document[key]["cac:Party"]
            self.assertEqual(
                len(
                    party_node["cac:PartyLegalEntity"]["cbc:RegistrationName"]["_text"]
                ),
                200,
            )
            address = party_node["cac:PostalAddress"]
            self.assertEqual(len(address["cbc:CityName"]["_text"]), 50)
            self.assertEqual(len(address["cbc:PostalZone"]["_text"]), 20)

    def test_a_document_with_nothing_over_the_limit_is_untouched(self):
        document = {"cbc:ID": {"_text": "F-0001"}}
        self.ubl._ro_apply_length_limits(document)
        self.assertEqual(document["cbc:ID"]["_text"], "F-0001")
