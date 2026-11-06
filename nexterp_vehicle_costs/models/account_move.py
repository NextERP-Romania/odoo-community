# Copyright (C) 2014 Forest AND Biomass Romania SA
# Copyright (C) 2019 OdooERP Romania SRL
# Copyright (C) 2024 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/14.0/legal/licenses/licenses.html#).


from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def button_cancel(self):
        # A cancelled vendor bill is no longer a cost of the vehicle: drop the
        # service logs account_fleet made from its lines when it was posted
        # (posting it again makes them anew).
        res = super().button_cancel()
        self.sudo().line_ids.vehicle_log_service_ids.with_context(
            ignore_linked_bill_constraint=True
        ).unlink()
        return res
