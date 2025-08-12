from odoo import models


class OutstandingStatement(models.AbstractModel):
    """Model of Outstanding Statement"""

    _inherit = "report.partner_statement.outstanding_statement"

    def _get_account_display_lines(
        self, company_id, partner_ids, date_start, date_end, account_type
    ):
        res = dict(map(lambda x: (x, []), partner_ids))
        partners = tuple(partner_ids)
        # pylint: disable=E8103
        self.env.cr.execute(
            """
        WITH Q1 as ({}),
             Q2 AS ({}),
             Q3 AS ({})
        SELECT partner_id, currency_id, move_id, date, date_maturity, debit,
            credit, amount, open_amount, COALESCE(name, '') as name,
            COALESCE(ref, '') as ref, blocked, id
        FROM Q3
        ORDER BY date, date_maturity, move_id""".format(
                self._display_outstanding_lines_sql_q1(
                    partners, date_end, account_type
                ),
                self._display_outstanding_lines_sql_q2("Q1"),
                self._display_outstanding_lines_sql_q3("Q2", company_id),
            )
        )
        for row in self.env.cr.dictfetchall():
            if row["date_maturity"] > date_end:
                row["next"] = True
            res[row.pop("partner_id")].append(row)
        return res

    # def _add_currency_line(self, line, currency):
    #     if float_is_zero(line["open_amount"], precision_rounding=currency.rounding):
    #         if line.get('next'):
    #             return [line]
    #         return []
    #     return [line]
