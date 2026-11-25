# Copyright 2026 NextERP Romania SRL
import base64
import re

from odoo import SUPERUSER_ID, api

_DATE = re.compile(rb'dataTransport="(\d{4}-\d{2}-\d{2})"')


def migrate(cr, version):
    """The new eTransport Transport Start got today's date on every record;
    where a notification was sent, put back its dataTransport (read from the
    latest sent XML that carries one: deletion / confirmation / vehicle
    change XMLs do not)."""
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    records = env["stock.picking"].search(
        [("l10n_ro_edi_stock_document_ids", "!=", False)]
    )
    for record in records:
        for document in record.l10n_ro_edi_stock_document_ids.sorted():
            if not document.attachment:
                continue
            match = _DATE.search(base64.b64decode(document.attachment))
            if match:
                cr.execute(
                    "UPDATE stock_picking SET l10n_ro_edi_stock_transport_date = %s "
                    "WHERE id = %s",
                    (match.group(1).decode(), record.id),
                )
                break
