# Copyright 2020 NextERP Romania
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    def _make_payments_inv(self, date, company_ids):
        # trebuie creat un jurnal de tipul  cash/bank cu numele de payment_invoice
        invoices = self.env["account.move"].search(
            [
                (
                    "move_type",
                    "in",
                    ["out_invoice", "in_invoice", "out_refund", "in_refund"],
                ),
                ("state", "in", ["posted"]),
                ("payment_state", "in", ["not_paid", "partial"]),
                ("date", "<", date),
                ("company_id", "in", company_ids),
            ]
        )
        journal = self.env["account.journal"].search(
            [("name", "=", "payment_invoice")], limit=1
        )

        payment_method = journal.inbound_payment_method_line_ids[0]
        for invoice in invoices[:100]:
            if invoice.move_type in ["out_invoice", "out_refund"]:
                payment_method = journal.inbound_payment_method_line_ids[0]
            else:
                payment_method = journal.outbound_payment_method_line_ids[0]
            try:
                payment_data = {
                    "payment_date": invoice.date,
                    # 'amount': amount,
                    "journal_id": journal.id,  # Replace with the correct journal ID
                    "currency_id": invoice.currency_id.id,  # Replace with the correct currency ID
                    "payment_method_line_id": payment_method.id,
                }
                payment = (
                    self.env["account.payment.register"]
                    .with_context(active_model="account.move", active_ids=[invoice.id])
                    .create(payment_data)
                    ._create_payments()
                )
                invoice.payment_id = payment.id

            except Exception as e:
                _logger.warning(f"Error processing invoice {invoice.id}: {e}")
                continue
