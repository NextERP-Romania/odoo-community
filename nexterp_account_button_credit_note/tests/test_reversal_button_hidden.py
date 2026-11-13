# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Taking "Reverse and Create Invoice" off the credit-note dialog.

That button cancels the invoice and opens a copy to edit, which is not how a
Romanian credit note works: the original stays, the credit note stands beside
it. Leaving only "Reverse" keeps people out of that path.
"""

from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestReversalButtonHidden(TransactionCase):
    def _arch(self):
        return etree.fromstring(
            self.env["account.move.reversal"].get_view(
                self.env.ref("account.view_account_move_reversal").id
            )["arch"]
        )

    def test_the_reverse_and_modify_button_is_hidden(self):
        (button,) = self._arch().xpath("//button[@name='modify_moves']")
        self.assertEqual(button.get("invisible"), "1")

    def test_the_plain_reverse_button_is_still_there(self):
        (button,) = self._arch().xpath("//button[@name='refund_moves']")
        self.assertNotEqual(button.get("invisible"), "1")
