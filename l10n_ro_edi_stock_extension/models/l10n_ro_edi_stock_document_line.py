# Copyright 2026 NextERP Romania SRL
from odoo import api, fields, models

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

    def _l10n_ro_edi_stock_parents(self):
        """Records whose eTransport notification this line is part of."""
        return self.picking_id

    def _l10n_ro_edi_stock_check_parents_not_sent(self):
        self._l10n_ro_edi_stock_parents()._l10n_ro_edi_stock_check_not_sent()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._l10n_ro_edi_stock_check_parents_not_sent()
        return records

    def write(self, vals):
        self._l10n_ro_edi_stock_check_parents_not_sent()
        res = super().write(vals)
        self._l10n_ro_edi_stock_check_parents_not_sent()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_l10n_ro_edi_stock_sent(self):
        self._l10n_ro_edi_stock_check_parents_not_sent()
