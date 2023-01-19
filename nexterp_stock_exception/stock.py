# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later

from odoo import api, models


class StockPicking(models.Model):
    _inherit = ["stock.picking", "base.exception"]
    _name = "stock.picking"

    def button_validate(self):
        if self.detect_exceptions() and not self.ignore_exception:
            return self._popup_exceptions()
        return super().button_validate()
