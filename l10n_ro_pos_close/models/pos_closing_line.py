# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/20.0/legal/licenses/licenses.html#).

from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero

CLOSING_REASONS = [
    ("wrong_method", "Takings recorded on another payment method"),
    ("miscount", "Counting error at closing"),
    ("shortage", "Takings missing"),
    ("surplus", "Surplus without a known origin"),
    ("other", "Other"),
]


class PosClosingLine(models.Model):
    """What one payment method was worth at the closing of a session.

    Core compares the amount the register recorded with the amount the cashier
    counted, posts the difference to the profit or loss account of the journal
    and forgets both numbers. The report of differences needs them, so they are
    kept here, one record per payment method, together with the reason the
    cashier gives for the gap.
    """

    _name = "l10n.ro.pos.closing.line"
    _description = "POS Closing Control Line"
    _order = "session_id desc, payment_method_type, payment_method_id"

    session_id = fields.Many2one(
        "pos.session",
        required=True,
        ondelete="cascade",
        index=True,
    )
    company_id = fields.Many2one(
        related="session_id.company_id",
        store=True,
    )
    currency_id = fields.Many2one(
        related="session_id.currency_id",
    )
    payment_method_id = fields.Many2one(
        "pos.payment.method",
        required=True,
        ondelete="restrict",
    )
    payment_method_type = fields.Selection(
        related="payment_method_id.type",
        store=True,
    )
    expected_amount = fields.Monetary(
        help="Amount the point of sale recorded on this payment method: the "
        "payments of the session for a bank method, the balance the cash "
        "drawer should hold for the cash method.",
    )
    counted_amount = fields.Monetary(
        help="Amount the cashier declared for this payment method when "
        "closing the session.",
    )
    difference = fields.Monetary(
        compute="_compute_difference",
        store=True,
        help="Counted less expected: a positive amount is a surplus, a "
        "negative one a shortage.",
    )
    has_difference = fields.Boolean(
        compute="_compute_difference",
        store=True,
    )
    reason = fields.Selection(
        selection=CLOSING_REASONS,
        help="Cause of the difference, as established when the session was "
        "closed. Printed on the report of differences.",
    )
    note = fields.Text(
        string="Explanation",
        help="Explanation of this difference, printed on the report. For "
        "example: the order was cashed in on the card method while the "
        "money was in fact taken in cash.",
    )

    @api.depends("expected_amount", "counted_amount")
    def _compute_difference(self):
        for line in self:
            rounding = line.currency_id.rounding or 0.01
            difference = line.counted_amount - line.expected_amount
            line.difference = difference
            line.has_difference = not float_is_zero(
                difference, precision_rounding=rounding
            )
