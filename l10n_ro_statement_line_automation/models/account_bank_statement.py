# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    l10n_ro_auto_statement = fields.Boolean(
        string="Daily Statement Created Automatically",
        copy=False,
        readonly=True,
        help="Statement opened by the module for the lines of one banking day."
        " Its ending balance follows the lines that join it.",
    )


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        statement_obj = self.env["account.bank.statement"]
        for record in res:
            if (
                record.statement_id
                or not record.journal_id
                or record.company_id.country_id.code != "RO"
            ):
                continue
            # Join the statement of the day: one this module opened, or one
            # the user left incomplete. A complete statement entered by the
            # user (its ending balance checked against the bank) is closed.
            statement = statement_obj.search(
                [
                    ("journal_id", "=", record.journal_id.id),
                    ("company_id", "=", record.company_id.id),
                    ("date", "=", record.date),
                    "|",
                    ("l10n_ro_auto_statement", "=", True),
                    ("is_complete", "=", False),
                ],
                order="l10n_ro_auto_statement desc, id",
                limit=1,
            )
            if not statement:
                statement = statement_obj.create(
                    {
                        "journal_id": record.journal_id.id,
                        "date": record.date,
                        "name": record.date,
                        "l10n_ro_auto_statement": True,
                    }
                )
            record.statement_id = statement.id
            statement._compute_balance_end()
            # Only the statements opened here have their ending balance
            # follow the lines; the one the user typed is never rewritten.
            if statement.l10n_ro_auto_statement:
                statement._compute_balance_end_real()
        return res
