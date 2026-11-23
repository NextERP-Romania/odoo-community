# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model_create_multi
    def create(self, vals_list):
        """Give a draft name to the transfers of a company numbering at
        validation, so the operation type's sequence is not consumed now.

        The company is the one of the operation type, not the user's current
        company: a transfer created for another company follows its setting.
        """
        PickingType = self.env["stock.picking.type"]
        default_type = self.default_get(["picking_type_id"]).get("picking_type_id")
        for vals in vals_list:
            if vals.get("name", "/") != "/":
                continue
            picking_type = PickingType.browse(
                vals.get("picking_type_id") or default_type
            )
            company = picking_type.company_id or self.env.company
            if (
                company.stock_assign_number_in_process
                and company.draft_picking_sequence_id
            ):
                vals["name"] = company.draft_picking_sequence_id.next_by_id()
        return super().create(vals_list)

    def _has_draft_picking_name(self):
        self.ensure_one()
        sequence = self.company_id.draft_picking_sequence_id
        prefix = sequence.prefix or ""
        return bool(sequence) and (
            self.name == "/" or (prefix and self.name.startswith(prefix))
        )

    def _action_done(self):
        """Number the transfers when they are done, from the operation type's
        sequence, in the order they are validated."""
        self._check_company()
        for picking in self:
            if (
                picking.company_id.stock_assign_number_in_process
                and picking.picking_type_id.sequence_id
                and picking._has_draft_picking_name()
            ):
                picking.name = picking.picking_type_id.sequence_id.next_by_id()
        return super()._action_done()
