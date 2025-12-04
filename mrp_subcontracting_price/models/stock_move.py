from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        subcontracting_prod_moves = self.filtered(
            lambda move: move.is_in
            and move.move_dest_ids
            and move.state == "done"
            and move.move_dest_ids.is_subcontract
        )
        if subcontracting_prod_moves:
            subcontracting_prod_moves.move_dest_ids._set_value()
        return res

    def _get_value_data(
        self,
        forced_std_price=False,
        at_date=False,
        ignore_manual_update=False,
        add_extra_value=True,
    ):
        res = super()._get_value_data(
            forced_std_price=forced_std_price,
            at_date=at_date,
            ignore_manual_update=ignore_manual_update,
            add_extra_value=add_extra_value,
        )
        if (
            self.is_in
            and self.move_orig_ids
            and self.is_subcontract
            and self.state == "done"
            and all(m.state == "done" for m in self.move_orig_ids)
        ):
            origin_data = self._get_value_from_origin_move(self.quantity)
            if origin_data:
                return origin_data
        return res
