# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""An invoice already in the SPV is corrected with a credit note, never by
taking it back to draft or cancelling it."""

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestSpvLock(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()

    def _invoice(self, spv_state=None, move_type="out_invoice"):
        move = self.init_invoice(move_type, amounts=[100.0], post=True)
        if spv_state:
            self.env["l10n_ro_edi.document"].sudo().create(
                {"invoice_id": move.id, "state": spv_state}
            )
        return move

    def test_a_validated_invoice_cannot_go_back_to_draft(self):
        move = self._invoice("invoice_validated")
        with self.assertRaises(UserError):
            move.button_draft()
        with self.assertRaises(UserError):
            move.button_cancel()
        self.assertEqual(move.state, "posted")

    def test_a_sent_credit_note_cannot_go_back_to_draft(self):
        move = self._invoice("invoice_sent", move_type="out_refund")
        with self.assertRaises(UserError):
            move.button_draft()

    def test_a_refused_invoice_can_be_corrected_and_sent_again(self):
        move = self._invoice("invoice_refused")
        move.button_draft()
        self.assertEqual(move.state, "draft")

    def test_an_invoice_not_sent_can_go_back_to_draft(self):
        move = self._invoice()
        move.button_draft()
        self.assertEqual(move.state, "draft")

    def test_a_validated_invoice_is_still_reversed_by_a_credit_note(self):
        move = self._invoice("invoice_validated")
        reversal = move._reverse_moves(cancel=True)
        self.assertEqual(reversal.move_type, "out_refund")
        self.assertEqual(move.state, "posted")

    def test_flow_from_draft_to_validated_then_corrected_by_credit_note(self):
        """Draft is free (edit, delete); posted and sent it is locked; once
        validated the only way back is a credit note, and the chatter stays
        writable throughout."""
        draft = self.init_invoice("out_invoice", amounts=[50.0])
        draft.ref = "editat in ciorna"
        draft.unlink()
        self.assertFalse(draft.exists())

        move = self._invoice()
        self.assertEqual(move.state, "posted")
        self.assertTrue(move.line_ids)
        self.assertEqual(move.amount_untaxed, 100.0)
        document = (
            self.env["l10n_ro_edi.document"]
            .sudo()
            .create({"invoice_id": move.id, "state": "invoice_sent"})
        )
        self.assertEqual(move.l10n_ro_edi_state, "invoice_sent")
        for action in (move.button_draft, move.button_cancel):
            with self.assertRaises(UserError):
                action()
        # The SPV answer replaces the sent document by the validated one.
        document.unlink()
        self.env["l10n_ro_edi.document"].sudo().create(
            {"invoice_id": move.id, "state": "invoice_validated"}
        )
        self.assertEqual(move.l10n_ro_edi_state, "invoice_validated")
        with self.assertRaises(UserError):
            move.button_draft()
        self.assertEqual(move.state, "posted")
        move.message_post(body="Nota dupa validare")
        refund = move._reverse_moves(cancel=True)
        self.assertEqual(refund.state, "posted")
        self.assertEqual(refund.amount_untaxed, 100.0)
        self.assertEqual(move.payment_state, "reversed")
