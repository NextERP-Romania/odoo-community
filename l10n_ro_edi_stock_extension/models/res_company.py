# Copyright 2026 NextERP Romania SRL
import logging

from odoo import api, fields, models

from .etransport_api_extra import ETransportAPIExtra

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = "res.company"

    l10n_ro_edi_stock_default_price_source = fields.Selection(
        selection=[
            ("auto", "Automatic (by operation)"),
            ("cost", "Cost price (standard_price)"),
            ("purchase", "Purchase order price"),
            ("sale", "Sale order price"),
            ("list", "Product list price"),
        ],
        default="auto",
        string="Default eTransport Price Source",
    )

    l10n_ro_edi_stock_list_days = fields.Integer(
        string="List Sync Days",
        default=14,
        help="Number of days for the LIST cron job (1-60).",
    )

    l10n_ro_edi_stock_list_enabled = fields.Boolean(
        string="Automatic List Sync",
        default=False,
        help="Enable the cron job calling the LIST service for reconciliation.",
    )

    @api.model
    def _l10n_ro_edi_stock_cron_list_sync(self):
        """Called by cron. Iterates RO companies with sync enabled and logs
        notifications with errors or unknown to Odoo (possibly declared via
        the ANAF web app).
        """
        companies = self.search(
            [
                ("account_fiscal_country_id.code", "=", "RO"),
                ("l10n_ro_edi_stock_list_enabled", "=", True),
                ("l10n_ro_edi_access_token", "!=", False),
            ]
        )
        for company in companies:
            try:
                self._l10n_ro_edi_stock_list_sync_one(company)
            except Exception as e:
                _logger.exception("LIST error for %s: %s", company.name, e)

    def _l10n_ro_edi_stock_list_sync_one(self, company):
        days = max(1, min(60, company.l10n_ro_edi_stock_list_days or 14))
        result = ETransportAPIExtra().get_list(company_id=company, days=days)
        if "error" in result:
            _logger.warning("LIST ANAF (%s): %s", company.name, result["error"])
            return
        # ANAF returns the records under "mesaje" (legacy "inregistrari" kept as
        # a fallback). Using the wrong key silently yields an empty list.
        rows = (
            result["content"]
            if isinstance(result["content"], list)
            else (
                result["content"].get("mesaje")
                or result["content"].get("inregistrari")
                or []
            )
        )
        if not rows:
            return

        # A UIT can sit either on a transfer or on a batch transfer, so both
        # models are reconciled against the ANAF list.
        uits = [r.get("uit") for r in rows if r.get("uit")]
        records_by_uit = {}
        for model in ("stock.picking", "stock.picking.batch"):
            for record in (
                self.env[model]
                .sudo()
                .search(
                    [
                        ("company_id", "=", company.id),
                        ("l10n_ro_edi_stock_document_uit", "in", uits),
                    ]
                )
            ):
                records_by_uit.setdefault(record.l10n_ro_edi_stock_document_uit, record)

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
