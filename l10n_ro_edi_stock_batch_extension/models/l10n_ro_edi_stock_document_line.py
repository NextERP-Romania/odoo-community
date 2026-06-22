# Copyright 2026 NextERP Romania SRL
from odoo import fields, models


class L10nRoEdiStockDocumentLine(models.Model):
    _inherit = "l10n.ro.edi.stock.document.line"

    batch_id = fields.Many2one(
        comodel_name="stock.picking.batch",
        string="Batch Transfer",
        ondelete="cascade",
        index=True,
    )
