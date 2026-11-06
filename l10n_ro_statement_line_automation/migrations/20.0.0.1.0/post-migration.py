# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    # The daily statements opened before the flag existed are named after
    # their date: mark them so the lines of that day keep joining them.
    cr.execute(
        """
        UPDATE account_bank_statement
           SET l10n_ro_auto_statement = TRUE
         WHERE name = date::text
        """
    )
