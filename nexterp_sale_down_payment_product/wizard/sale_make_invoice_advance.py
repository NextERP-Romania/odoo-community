# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def _get_down_payment_account(self, product):
        # Down payment base lines have no product, use the one from settings
        if not product:
            product = self.company_id.l10n_ro_sale_down_payment_product_id
        return super()._get_down_payment_account(product)
