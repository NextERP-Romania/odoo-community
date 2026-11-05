# Copyright 2026 NextERP Romania SRL
from odoo import fields, models


class L10nRoEdiStockPreviousNotification(models.Model):
    _inherit = "l10n.ro.edi.stock.previous.notification"

    batch_id = fields.Many2one(
        comodel_name="stock.picking.batch",
        string="Batch Transfer",
        ondelete="cascade",
        index=True,
    )

    def _l10n_ro_edi_stock_check_parents_not_sent(self):
        res = super()._l10n_ro_edi_stock_check_parents_not_sent()
        self.batch_id._l10n_ro_edi_stock_check_not_sent()
        return res
