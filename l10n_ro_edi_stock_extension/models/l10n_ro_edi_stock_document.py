# Copyright 2026 NextERP Romania SRL
from odoo import fields, models

EXTRA_DOCUMENT_STATES = [
    ("stock_deleted", "Deleted"),
    ("stock_confirmed", "Confirmed"),
    ("stock_vehicle_modified", "Vehicle Modified"),
]

# A UIT in one of these states is known to ANAF: the transfer it covers must
# not disappear from Odoo until the notification is deleted (DEL).
LIVE_UIT_STATES = (
    "stock_sent",
    "stock_validated",
    "stock_confirmed",
    "stock_vehicle_modified",
)

# States from which ANAF accepts a deletion / confirmation / vehicle change.
UIT_ACTION_STATES = ("stock_validated", "stock_vehicle_modified")


def l10n_ro_edi_stock_effective_document(documents):
    """The document that tells where the UIT stands at ANAF.

    A failed attempt (validation error, refused correction, unreachable
    server) does not undo what ANAF already has, so failed documents are
    skipped and the latest one before them counts.
    """
    for document in documents.sorted():
        if document.state != "stock_sending_failed":
            return document
    return documents.browse()


def l10n_ro_edi_stock_live_uit_document(documents):
    """The document of a UIT still alive at ANAF, or an empty recordset."""
    document = l10n_ro_edi_stock_effective_document(documents)
    return document if document.state in LIVE_UIT_STATES else documents.browse()


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
