# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _get_report_lang(self):
        if (
            self.company_id.picking_report_lang_company
            and self.picking_type_code != "outgoing"
        ):
            return self.company_id.partner_id.lang
        return super()._get_report_lang()
