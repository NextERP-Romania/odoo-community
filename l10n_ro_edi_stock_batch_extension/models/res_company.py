# Copyright 2026 NextERP Romania SRL
import logging

from odoo import models

from odoo.addons.l10n_ro_edi_stock_extension.models.etransport_api_extra import (
    ETransportAPIExtra,
)

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    def _l10n_ro_edi_stock_list_sync_one(self, company):
        # OVERRIDE l10n_ro_edi_stock_extension
        # Reconcile the ANAF LIST against both pickings and batch transfers
        # (batch UITs live on stock.picking.batch). Reimplemented in a single
        # API call instead of chaining super() to avoid a second request.
        days = max(1, min(60, company.l10n_ro_edi_stock_list_days or 14))
        result = ETransportAPIExtra().get_list(company_id=company, days=days)
        if "error" in result:
            _logger.warning("LIST ANAF (%s): %s", company.name, result["error"])
            return
        rows = (
            result["content"]
            if isinstance(result["content"], list)
            else result["content"].get("inregistrari", [])
        )
        if not rows:
            return

        uits = [r.get("uit") for r in rows if r.get("uit")]
        records_by_uit = {}
        for picking in (
            self.env["stock.picking"]
            .sudo()
            .search(
                [
                    ("company_id", "=", company.id),
                    ("l10n_ro_edi_stock_document_uit", "in", uits),
                ]
            )
        ):
            records_by_uit.setdefault(picking.l10n_ro_edi_stock_document_uit, picking)
        for batch in (
            self.env["stock.picking.batch"]
            .sudo()
            .search(
                [
                    ("company_id", "=", company.id),
                    ("l10n_ro_edi_stock_document_uit", "in", uits),
                ]
            )
        ):
            records_by_uit.setdefault(batch.l10n_ro_edi_stock_document_uit, batch)

        for row in rows:
            record = records_by_uit.get(row.get("uit"))
            if not record:
                continue
            if row.get("stare") == "ERR":
                messages = "\n".join(
                    f"[{m.get('tip')}] {m.get('mesaj')}"
                    for m in (row.get("mesaje") or [])
                )
                record._message_log(
                    body=(
                        f"ANAF LIST returned errors for this notification:\n{messages}"
                    )
                )
