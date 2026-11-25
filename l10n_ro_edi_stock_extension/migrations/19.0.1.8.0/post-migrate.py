# Copyright 2026 NextERP Romania SRL
import base64
import re

from odoo import SUPERUSER_ID, api

_DATE = re.compile(rb'dataTransport="(\d{4}-\d{2}-\d{2})"')


def migrate(cr, version):
    """The new eTransport Transport Start got today's date on every record;
    where a UIT is alive, put back the date sent to ANAF (the validity is
    computed from it)."""
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    for record in env["stock.picking"].search(
        [("l10n_ro_edi_stock_document_ids", "!=", False)]
    ):
        document = record._l10n_ro_edi_stock_live_uit_document()
        validated = document and record._l10n_ro_edi_stock_get_last_document(
            "stock_validated"
        )
        if not validated or not validated.attachment:
            continue
        match = _DATE.search(base64.b64decode(validated.attachment))
        if match:
            cr.execute(
                "UPDATE stock_picking SET l10n_ro_edi_stock_transport_date = %s "
                "WHERE id = %s",
                (match.group(1).decode(), record.id),
            )
