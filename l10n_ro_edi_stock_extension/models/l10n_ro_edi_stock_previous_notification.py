# Copyright 2026 NextERP Romania SRL
from odoo import fields, models


class L10nRoEdiStockPreviousNotification(models.Model):
    _name = "l10n.ro.edi.stock.previous.notification"
    _description = "eTransport previous notification (operations 60/70)"
    _order = "id"

    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Transfer",
        ondelete="cascade",
        index=True,
    )
    uit = fields.Char(string="Previous UIT", size=16, required=True)
    remarks = fields.Char(size=200)
    declarant_ref = fields.Char(string="Declarant Reference", size=50)
