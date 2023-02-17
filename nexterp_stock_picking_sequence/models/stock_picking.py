# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).


from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"


    @api.model
    def create(self, vals):
        assign_number = self.env.company.stock_assign_number_in_process
        if assign_number and self.env.company.draft_picking_sequence_id:
            vals['name'] = f"{self.env.company.draft_picking_sequence_id.next_by_id()}"        
        res =  super().create(vals)
        
        return res

    def _action_done(self):
        """Assign number to pickings that are from a company with this setting.

        Assign a number to pickings that are from a company with the setting
        stock_assign_number_in_process enabled and that have a name that starts
        with "Draft-" or is equal to "/". This is done by calling the next_by_id
        method of the sequence defined in the picking type.
        """
        self._check_company()
        for picking in self:
            draft_sequence_prefix = (
                picking.company_id.draft_picking_sequence_id 
                and picking.company_id.draft_picking_sequence_id.prefix
            ) or ""
            if (
                picking.picking_type_id.sequence_id
                and picking.company_id.stock_assign_number_in_process
                and picking.company_id.draft_picking_sequence_id
                and (picking.name.startswith(draft_sequence_prefix) or picking.name == "/")
            ):
                picking.name = picking.picking_type_id.sequence_id.next_by_id()
        return super()._action_done()
