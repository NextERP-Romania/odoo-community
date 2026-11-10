# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError

# Same definitions as l10n_ro_account_enterprise, so the fields merge cleanly
# when both modules are installed.
SEQUENCE_TYPE = [
    ("normal", "Invoice"),
    ("autoinv1", "Customer Auto Invoicing"),
    ("autoinv2", "Supplier  Auto Invoicing"),
]


class AccountJournal(models.Model):
    _inherit = "account.journal"

    l10n_ro_partner_id = fields.Many2one("res.partner", "Ro Partner", default=None)
    l10n_ro_sequence_type = fields.Selection(
        selection=SEQUENCE_TYPE, string="Ro Sequence Type", default="normal"
    )

    def _register_hook(self):
        super()._register_hook()
        # l10n_ro_account_enterprise shows the same fields on the journal
        # form: keep ours only while it is not there, so they never show twice.
        view = self.env.ref(
            "l10n_ro_edi_autoinvoice.view_account_journal_form",
            raise_if_not_found=False,
        )
        other_view = self.env.ref(
            "l10n_ro_account_enterprise.view_account_journal_form_inheritedD394",
            raise_if_not_found=False,
        )
        if view and view.active == bool(other_view):
            view.sudo().active = not other_view

    def write(self, vals):
        locked = {"l10n_ro_sequence_type", "l10n_ro_partner_id"} & set(vals)
        if locked:
            for journal in self:
                changed = [
                    fname
                    for fname in locked
                    if journal._fields[fname].convert_to_write(journal[fname], journal)
                    != vals[fname]
                ]
                if changed and self.env["account.move"].sudo().search_count(
                    [("journal_id", "=", journal.id), ("state", "=", "posted")],
                    limit=1,
                ):
                    raise UserError(
                        self.env._(
                            "The journal %(journal)s already has posted entries:"
                            " its self-invoicing type and partner can no longer"
                            " be changed.",
                            journal=journal.display_name,
                        )
                    )
        return super().write(vals)

    @api.onchange("l10n_ro_sequence_type")
    def onchange_l10n_ro_sequence_type(self):
        self.is_self_billing = self.l10n_ro_sequence_type in ("autoinv1", "autoinv2")
