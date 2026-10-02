# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/20.0/legal/licenses/licenses.html#).

from odoo import api, models

REPORT = "l10n_ro_account_bank_statement_report.action_report_l10n_ro_account_statement"


class PosConfig(models.Model):
    _inherit = "pos.config"

    @api.model
    def _load_pos_data_read(self, records, config):
        """Tell the till the name of the report it has to ask for.

        The register form belongs to the Romanian localisation, so a till
        anywhere else has no such report. Sending the name rather than
        hard-coding it lets the screen simply not offer printing where there
        is nothing to print.
        """
        read_records = super()._load_pos_data_read(records, config)
        report = self.env.ref(REPORT, raise_if_not_found=False)
        for values in read_records:
            values["_pos_cash_register_report"] = report.xml_id if report else False
        return read_records

    def pos_cash_register_sessions(self, limit=60):
        """The sessions of this point of sale, newest first.

        Asked for when the screen is opened rather than loaded with the
        session: a register is looked at now and then, and a till that
        carried every session it ever had would carry them for nothing.

        What comes back is the register in figures, so the list answers the
        question without opening the document:

        - ``opening`` is the drawer counted when the session opened;
        - ``movements`` is everything written against it afterwards;
        - ``expected`` is the two added up -- what the drawer should hold;
        - ``counted`` is what was actually counted at the close;
        - ``difference`` is the gap between those last two, which is the
          only figure here that can be anything but zero by surprise.

        The opening and the closing are NOT compared against the session's
        own `opening_balance` / `closing_balance`: those are related fields
        onto this very statement, so the two could never disagree. The gap
        worth showing is the counted drawer against the movements.
        """
        self.ensure_one()
        sessions = self.env["pos.session"].search(
            [("config_id", "=", self.id)], order="start_at desc, id desc", limit=limit
        )
        currency = self.currency_id
        rows = []
        for session in sessions:
            statement = session.bank_statement_id
            opening = statement.balance_start
            expected = statement.balance_end
            counted = statement.balance_end_real
            rows.append(
                {
                    "id": session.id,
                    "name": session.name,
                    "state": session.state,
                    "start_at": session.start_at,
                    "stop_at": session.stop_at,
                    "user": session.user_id.display_name or "",
                    "statement_id": statement.id or False,
                    "opening": opening,
                    "movements": expected - opening,
                    "expected": expected,
                    "counted": counted,
                    "difference": counted - expected,
                    "balanced": statement
                    and currency.is_zero(counted - expected)
                    or not statement,
                }
            )
        return rows
