# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).


from odoo import api, fields, models


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
        """Assign number to pickings that are from a company with this setting.

        Assign a number to pickings that are from a company with the setting
        stock_assign_number_in_process enabled and that have a name that starts
        with "Draft-" or is equal to "/". This is done by calling the next_by_id
        method of the sequence defined in the picking type.
        """
        self._check_company()
        for picking in self:
            if (
                picking.picking_type_id.sequence_id
                and picking.company_id.stock_assign_number_in_process
                and (picking.name.startswith("Draft-") or picking.name == "/")
            ):
                picking.name = picking.picking_type_id.sequence_id.next_by_id()
        return super()._action_done()

    def _create_backorder(self):
        backorders = super()._create_backorder()
        for picking in backorders:
            if (
                picking.name == "/"
                and picking.company_id.stock_assign_number_in_process
            ):
                picking.name = f"Draft-{fields.Datetime.now().timestamp()}"
        return backorders
