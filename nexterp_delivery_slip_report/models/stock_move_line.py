# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_aggregated_product_quantities(self, **kwargs):
        agg_move_lines = super()._get_aggregated_product_quantities(**kwargs)

        for aggregated_move_line in agg_move_lines:
            line = agg_move_lines[aggregated_move_line]
            line["report_precision"] = line["product_uom"].report_precision
        return agg_move_lines

    def _get_aggregated_properties(self, move_line=False, move=False):
        # Get product name without default_code
        res = super()._get_aggregated_properties(move_line=move_line, move=move)
        move = move or move_line.move_id
        if move.company_id.delivery_slip_report_only_name:
            res["name"] = move.product_id.name
        return res

    def _get_report_lang(self):
        return (
            self.move_ids
            and self.move_ids[0].partner_id.lang
            or self.partner_id.lang
            or self.env.lang
        )
