# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/20.0/legal/licenses/licenses.html#).

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero
from odoo.tools.misc import format_amount

from .pos_closing_line import CLOSING_REASONS


class PosSession(models.Model):
    _inherit = "pos.session"

    l10n_ro_closing_line_ids = fields.One2many(
        "l10n.ro.pos.closing.line",
        "session_id",
        string="Closing Control",
        readonly=True,
    )
    l10n_ro_closing_surplus = fields.Monetary(
        string="Surplus",
        compute="_compute_l10n_ro_closing_difference",
        store=True,
        help="Total of the payment methods counted above what the register recorded.",
    )
    l10n_ro_closing_shortage = fields.Monetary(
        string="Shortage",
        compute="_compute_l10n_ro_closing_difference",
        store=True,
        help="Total of the payment methods counted below what the register "
        "recorded, as a positive amount.",
    )
    l10n_ro_closing_difference = fields.Monetary(
        string="Net Difference",
        compute="_compute_l10n_ro_closing_difference",
        store=True,
        help="Surpluses less shortages. It is zero when a difference is only "
        "takings that landed on the wrong payment method.",
    )
    l10n_ro_has_closing_difference = fields.Boolean(
        string="Has Closing Difference",
        compute="_compute_l10n_ro_closing_difference",
        store=True,
    )
    l10n_ro_closing_notes = fields.Text(
        string="Explanatory Note",
        help="Note of the cashier on the differences found at closing, "
        "printed at the end of the report of differences.",
    )
    l10n_ro_closing_explanations = fields.Json(
        string="Closing Explanations",
        readonly=True,
        help="What the cashier typed in the register for each payment method "
        "that did not match, kept until the closing writes it on the control "
        "lines.",
    )

    @api.depends(
        "l10n_ro_closing_line_ids.difference",
        "l10n_ro_closing_line_ids.has_difference",
    )
    def _compute_l10n_ro_closing_difference(self):
        for session in self:
            differences = session.l10n_ro_closing_line_ids.mapped("difference")
            surplus = sum(amount for amount in differences if amount > 0)
            shortage = -sum(amount for amount in differences if amount < 0)
            session.l10n_ro_closing_surplus = surplus
            session.l10n_ro_closing_shortage = shortage
            session.l10n_ro_closing_difference = surplus - shortage
            session.l10n_ro_has_closing_difference = any(
                session.l10n_ro_closing_line_ids.mapped("has_difference")
            )

    # -- capture of the closing control -----------------------------------

    def close_session_from_ui(self, payment_method_closing=None):
        """Keep what the cashier counted, then close as core does.

        The counted amounts only exist as the argument of this call, so they
        are read on the way through: the flag tells the cash handler below
        that this is the closing call and not the opening one.
        """
        payment_method_closing = payment_method_closing or {}
        session = self.with_context(l10n_ro_pos_closing=True)
        result = super(PosSession, session).close_session_from_ui(
            payment_method_closing
        )
        if result.get("status") and session.l10n_ro_has_closing_difference:
            session._l10n_ro_post_closing_difference_message()
        return result

    def _handle_cash_statement_entries(self, payment_method_closing=None):
        # Core calls this both when the session opens and when it closes, and
        # it is the last step that still sees the drawer as the session left
        # it: the correction line it posts is what makes the balance match the
        # count. The snapshot is taken before that, and after the sales have
        # reached the statement.
        payment_method_closing = payment_method_closing or {}
        if self.env.context.get("l10n_ro_pos_closing"):
            self._l10n_ro_record_closing_control(payment_method_closing)
        return super()._handle_cash_statement_entries(payment_method_closing)

    def _l10n_ro_record_closing_control(self, payment_method_closing):
        """Write one line per payment method settled at this closing."""
        self.ensure_one()
        self.l10n_ro_closing_line_ids.sudo().unlink()
        explanations = self.l10n_ro_closing_explanations or {}
        vals_list = []
        for method in self.payment_method_ids:
            if method.type not in ("cash", "bank"):
                continue
            counted = self._l10n_ro_counted_amount(method, payment_method_closing)
            if counted is None:
                continue
            vals_list.append(
                {
                    "session_id": self.id,
                    "payment_method_id": method.id,
                    "expected_amount": self._l10n_ro_expected_amount(method),
                    "counted_amount": counted,
                    **self._l10n_ro_explanation_values(
                        explanations.get(str(method.id))
                    ),
                }
            )
        if vals_list:
            self.env["l10n.ro.pos.closing.line"].sudo().create(vals_list)
        return True

    def _l10n_ro_explanation_values(self, explanation):
        """What the cashier typed in the register for one payment method.

        It comes from the browser, so the cause is only kept when it is one
        of ours; a cashier cannot invent a selection value.
        """
        explanation = explanation or {}
        reason = explanation.get("reason")
        return {
            "reason": reason if reason in dict(CLOSING_REASONS) else False,
            "note": explanation.get("note") or False,
        }

    def l10n_ro_set_closing_explanations(self, explanations=None, closing_note=None):
        """Keep what the cashier typed in the closing popup of the register.

        The register sends this just before it closes the session: the
        amounts are core's business, the reason they do not match is ours.
        Core collects a closing note in the same popup and then drops it on
        the way to the server, so that one is kept here as well.
        """
        self.ensure_one()
        values = {"l10n_ro_closing_explanations": explanations or {}}
        if closing_note is not None:
            values["closing_notes"] = closing_note
            values["l10n_ro_closing_notes"] = closing_note
        self.write(values)
        return True

    def _l10n_ro_counted_amount(self, method, payment_method_closing):
        """Amount the register declared, or ``None`` when it declared none.

        Core skips the reconciliation of a bank method the frontend left out
        of the closing, so there is nothing to compare for it either. The cash
        method is always settled, an uncounted drawer being counted as empty.
        """
        self.ensure_one()
        for key in (str(method.id), method.id):
            if key in payment_method_closing:
                return payment_method_closing[key] or 0.0
        return 0.0 if method.type == "cash" else None

    def _l10n_ro_expected_amount(self, method):
        """Amount the register recorded on this payment method."""
        self.ensure_one()
        if method.type == "cash":
            # The same balance core compares the count against: the opening
            # float, the cash in and out, and the cash takings of the session.
            if self.bank_statement_id:
                return self.bank_statement_id.balance_end
            return self.config_id._get_opening_balance()
        payments = self.order_ids.mapped("payment_ids").filtered(
            lambda payment, method=method: payment.payment_method_id == method
        )
        return sum(payments.mapped("amount"))

    def _l10n_ro_post_closing_difference_message(self):
        """Say in the chatter which methods did not match, and by how much."""
        self.ensure_one()
        items = Markup()
        for line in self.l10n_ro_closing_line_ids.filtered("has_difference"):
            items += Markup("<li>%s</li>") % self.env._(
                "%(method)s: counted %(counted)s against %(expected)s "
                "recorded, difference %(difference)s",
                method=line.payment_method_id.name,
                counted=format_amount(self.env, line.counted_amount, self.currency_id),
                expected=format_amount(
                    self.env, line.expected_amount, self.currency_id
                ),
                difference=format_amount(self.env, line.difference, self.currency_id),
            )
        body = Markup("<p>%s</p><ul>%s</ul>") % (
            self.env._(
                "Differences found at closing. Fill in their cause and print "
                "the report of differences."
            ),
            items,
        )
        self.message_post(body=body)

    # -- the report of differences ----------------------------------------

    def action_l10n_ro_closing_note(self):
        """Open the note where the cashier explains the differences."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Explanatory Note"),
            "res_model": "l10n.ro.pos.closing.note",
            "view_mode": "form",
            "target": "new",
            "context": {"default_session_id": self.id},
        }

    def action_l10n_ro_print_closing_report(self):
        self.ensure_one()
        if not self.l10n_ro_closing_line_ids:
            raise UserError(
                self.env._(
                    "The closing of %(session)s was not controlled by payment "
                    "method, so there is nothing to report. Only sessions "
                    "closed after this module was installed carry the amounts "
                    "the cashier counted.",
                    session=self.display_name,
                )
            )
        return self.env.ref(
            "l10n_ro_pos_close.action_report_pos_session_closing"
        ).report_action(self)

    def _l10n_ro_report_lines(self):
        """Lines of the report: the differences first, then the rest."""
        self.ensure_one()
        return self.l10n_ro_closing_line_ids.sorted(
            key=lambda line: (not line.has_difference, line.payment_method_id.name)
        )

    def _l10n_ro_is_balanced(self):
        """True when the surpluses cover the shortages to the last leu.

        That is the shape of takings cashed in on the wrong payment method:
        the till is right, the split between the methods is not.
        """
        self.ensure_one()
        return self.l10n_ro_has_closing_difference and float_is_zero(
            self.l10n_ro_closing_difference,
            precision_rounding=self.currency_id.rounding or 0.01,
        )
