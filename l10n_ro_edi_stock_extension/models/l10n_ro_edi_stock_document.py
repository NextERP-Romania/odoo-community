# Copyright 2026 NextERP Romania SRL
from odoo import fields, models

EXTRA_DOCUMENT_STATES = [
    ("stock_deleted", "Deleted"),
    ("stock_confirmed", "Confirmed"),
    ("stock_vehicle_modified", "Vehicle Modified"),
]


class L10nRoEdiStockDocument(models.Model):
    _inherit = "l10n_ro_edi.document"

    state = fields.Selection(
        selection_add=EXTRA_DOCUMENT_STATES,
        ondelete={k: "cascade" for k, _ in EXTRA_DOCUMENT_STATES},
    )

    # ANAF event type (NOT/COR/DEL/CON/MVH)
    l10n_ro_edi_stock_event_type = fields.Selection(
        selection=[
            ("NOT", "Notification"),
            ("COR", "Correction"),
            ("DEL", "Deletion"),
            ("CON", "Confirmation"),
            ("MVH", "Vehicle Modification"),
        ],
        string="Event Type",
    )

    l10n_ro_edi_stock_confirm_type = fields.Selection(
        selection=[
            ("10", "Confirmed"),
            ("20", "Partially confirmed"),
            ("30", "Refused"),
        ],
        string="Confirmation Type",
    )

    l10n_ro_edi_stock_modified_vehicle = fields.Char(string="Modified Vehicle Number")
    l10n_ro_edi_stock_modification_date = fields.Datetime(
        string="Vehicle Modification Date"
    )
