# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).


from odoo import api, models, fields


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def default_get(self, fields_list):
        defaults = super(StockPicking, self).default_get(fields_list)
        assign_number = self.env.company.stock_assign_number_in_process
        if assign_number:
            defaults["name"] = f"Draft-{fields.Datetime.now().timestamp()}"
        return defaults

    def _action_done(self):
        """Assign number to pickings that are from a company with this setting."""
        self._check_company()
        for picking in self:
            if (
                picking.picking_type_id.sequence_id
                and picking.company_id.stock_assign_number_in_process
                and picking.name.startswith("Draft-")
            ):
                picking.name = picking.picking_type_id.sequence_id.next_by_id()
        return super()._action_done()
