# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import fields, models
from odoo.tools.sql import column_exists, create_column


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_inter_company = fields.Boolean(
        related="move_id.is_inter_company", store=True, readonly=True, index=True
    )

    def _auto_init(self):
        """
        Create compute stored field is_inter_company
        here to avoid MemoryError on large databases.
        """
        cr = self.env.cr
        if not column_exists(cr, "account_move_line", "is_inter_company"):
            create_column(cr, "account_move_line", "is_inter_company", "boolean")
            if column_exists(cr, "account_move", "is_inter_company"):
                # pylint: disable=E8103
                cr.execute(
                    """
                    UPDATE account_move_line aml
                    SET is_inter_company = am.is_inter_company
                    FROM account_move am
                    WHERE aml.move_id = am.id;
                    """,
                )
            else:
                # pylint: disable=E8103
                cr.execute("UPDATE account_move_line SET is_inter_company = FALSE;")
        return super()._auto_init()
