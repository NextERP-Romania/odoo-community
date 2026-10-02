# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/20.0/legal/licenses/licenses.html#).

from odoo import Command, api, fields, models

from ..models.pos_closing_line import CLOSING_REASONS


class PosClosingNote(models.TransientModel):
    """Where the cashier explains the differences of a closed session.

    The session form is read only, as core left it, so the explanation is
    written here and from here the report is printed.
    """

    _name = "l10n.ro.pos.closing.note"
    _description = "POS Closing Explanatory Note"

    session_id = fields.Many2one(
        "pos.session",
        required=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        related="session_id.currency_id",
    )
    surplus = fields.Monetary(
        related="session_id.l10n_ro_closing_surplus",
    )
    shortage = fields.Monetary(
        related="session_id.l10n_ro_closing_shortage",
    )
    difference = fields.Monetary(
        related="session_id.l10n_ro_closing_difference",
    )
    note = fields.Text(
        string="Explanatory Note",
        help="Note printed at the end of the report of differences.",
    )
    line_ids = fields.One2many(
        "l10n.ro.pos.closing.note.line",
        "wizard_id",
        string="Payment Methods",
    )

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        session = self.env["pos.session"].browse(
            values.get("session_id") or self.env.context.get("default_session_id")
        )
        if not session:
            return values
        values["note"] = session.l10n_ro_closing_notes
        values["line_ids"] = [
            Command.create(
                {
                    "closing_line_id": line.id,
                    "reason": line.reason,
                    "note": line.note,
                }
            )
            for line in session._l10n_ro_report_lines()
        ]
        return values

    def action_save(self):
        self.ensure_one()
        self.session_id.l10n_ro_closing_notes = self.note
        for line in self.line_ids:
            line.closing_line_id.write(
                {
                    "reason": line.reason,
                    "note": line.note,
                }
            )
        return {"type": "ir.actions.act_window_close"}

    def action_save_and_print(self):
        self.ensure_one()
        self.action_save()
        return self.session_id.action_l10n_ro_print_closing_report()


class PosClosingNoteLine(models.TransientModel):
    _name = "l10n.ro.pos.closing.note.line"
    _description = "POS Closing Explanatory Note Line"
    _order = "id"

    wizard_id = fields.Many2one(
        "l10n.ro.pos.closing.note",
        required=True,
        ondelete="cascade",
    )
    closing_line_id = fields.Many2one(
        "l10n.ro.pos.closing.line",
        string="Closing Control Line",
        required=True,
        ondelete="cascade",
    )
    currency_id = fields.Many2one(
        related="closing_line_id.currency_id",
    )
    payment_method_id = fields.Many2one(
        related="closing_line_id.payment_method_id",
    )
    expected_amount = fields.Monetary(
        related="closing_line_id.expected_amount",
    )
    counted_amount = fields.Monetary(
        related="closing_line_id.counted_amount",
    )
    difference = fields.Monetary(
        related="closing_line_id.difference",
    )
    has_difference = fields.Boolean(
        related="closing_line_id.has_difference",
    )
    reason = fields.Selection(
        selection=CLOSING_REASONS,
    )
    note = fields.Text(
        string="Explanation",
        help="Explanation printed on the report for this payment method.",
    )
