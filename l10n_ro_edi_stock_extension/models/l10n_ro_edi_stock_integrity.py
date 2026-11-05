# Copyright 2026 NextERP Romania SRL
from odoo import models
from odoo.exceptions import UserError

from .l10n_ro_edi_stock_document import l10n_ro_edi_stock_live_uit_document


class L10nRoEdiStockIntegrityMixin(models.AbstractModel):
    """Guards shared by the records an eTransport notification is filed on
    (transfers, and batches in l10n_ro_edi_stock_batch_extension). They carry
    ``l10n_ro_edi_stock_document_ids`` and ``l10n_ro_edi_stock_state``."""

    _name = "l10n.ro.edi.stock.integrity.mixin"
    _description = "eTransport notification integrity"

    def _l10n_ro_edi_stock_live_uit_document(self):
        self.ensure_one()
        return l10n_ro_edi_stock_live_uit_document(self.l10n_ro_edi_stock_document_ids)

    def _l10n_ro_edi_stock_check_no_live_uit(self, action):
        for record in self:
            document = record._l10n_ro_edi_stock_live_uit_document()
            if document:
                raise UserError(
                    self.env._(
                        "%(record)s cannot be %(action)s: its eTransport "
                        "notification (UIT %(uit)s) is registered at ANAF. "
                        "Delete the notification first.",
                        record=record.display_name,
                        action=action,
                        uit=document.l10n_ro_edi_stock_uit,
                    )
                )

    def _l10n_ro_edi_stock_check_not_sent(self):
        if self.env.context.get("l10n_ro_edi_stock_skip_sent_lock"):
            return
        for record in self:
            if record.l10n_ro_edi_stock_state == "stock_sent":
                raise UserError(
                    self.env._(
                        "The eTransport data of %(record)s cannot be changed "
                        "while ANAF is processing its notification. Fetch the "
                        "status first.",
                        record=record.display_name,
                    )
                )
