# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import api, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            if not record.statement_id and res.company_id.country_id.code == "RO":
                if record.journal_id:
                    statement = self.env["account.bank.statement"].search(
                        [
                            ("journal_id", "=", record.journal_id.id),
                            ("date", "=", record.date),
                        ],
                        limit=1,
                    )
                    if not statement:
                        statement = self.env["account.bank.statement"].create(
                            {
                                "journal_id": record.journal_id.id,
                                "date": record.date,
                                "name": record.date,
                            }
                        )
                    record.statement_id = statement.id
                    record.statement_id._compute_balance_end()
                    record.statement_id._compute_balance_end_real()
        return res
