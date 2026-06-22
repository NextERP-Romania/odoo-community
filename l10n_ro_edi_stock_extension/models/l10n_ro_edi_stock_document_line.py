# Copyright 2026 NextERP Romania SRL
from odoo import fields, models

from .etransport_constants import DOCUMENT_TYPES


class L10nRoEdiStockDocumentLine(models.Model):
    _name = "l10n.ro.edi.stock.document.line"
    _description = "eTransport transport document line"
    _order = "document_date desc, id"

    picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Transfer",
        ondelete="cascade",
        index=True,
    )
    document_type = fields.Selection(
        selection=DOCUMENT_TYPES,
        required=True,
        default="30",
    )
    document_number = fields.Char(size=50)
    document_date = fields.Date(required=True)
    remarks = fields.Char(
        size=200,
        help="Required when document type is 'Other' (9999).",
    )
