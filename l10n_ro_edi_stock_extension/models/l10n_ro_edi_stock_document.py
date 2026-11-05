# Copyright 2026 NextERP Romania SRL
from odoo import fields, models

EXTRA_DOCUMENT_STATES = [
    ("stock_action_sent", "Action Sent"),
    ("stock_deleted", "Deleted"),
    ("stock_confirmed", "Confirmed"),
    ("stock_vehicle_modified", "Vehicle Modified"),
]

# A deletion / confirmation / vehicle change uploaded to ANAF waits in
# ``stock_action_sent`` until its processing status is fetched; then it moves
# to the state below, or to ``stock_sending_failed`` when ANAF refused it.
PENDING_ACTION_STATE = "stock_action_sent"
ACTION_FINAL_STATES = {
    "DEL": "stock_deleted",
    "CON": "stock_confirmed",
    "MVH": "stock_vehicle_modified",
}

# On uninstall the documents are kept, under the closest base state, so the
# trail of what was sent to ANAF survives:
# - a confirmation or a vehicle change leaves the UIT valid -> 'validated';
# - a deletion (or an action whose outcome is unknown) means the UIT can no
#   longer be relied upon -> 'error', with the original state in the message.
_UNINSTALL_STATE = {
    "stock_action_sent": "stock_sending_failed",
    "stock_deleted": "stock_sending_failed",
    "stock_confirmed": "stock_validated",
    "stock_vehicle_modified": "stock_validated",
}


def _document_state_ondelete(state):
    target = _UNINSTALL_STATE[state]
    if target == "stock_validated":
        return f"set {target}"

    def keep_as_error(documents):
        for document in documents:
            note = f"[{state} / {document.l10n_ro_edi_stock_event_type or ''}]"
            document.write(
                {
                    "state": target,
                    "message": f"{note} {document.message or ''}".strip(),
                }
            )

    return keep_as_error


# Same mapping for the state copied on transfers / batches.
RECORD_STATE_ONDELETE = {
    state: f"set {target}" for state, target in _UNINSTALL_STATE.items()
}

# A UIT in one of these states is known to ANAF: the transfer it covers must
# not disappear from Odoo until the notification is deleted (DEL). A pending
# action counts as live until ANAF has accepted it.
LIVE_UIT_STATES = (
    "stock_sent",
    "stock_action_sent",
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
        ondelete={k: _document_state_ondelete(k) for k, _ in EXTRA_DOCUMENT_STATES},
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
    l10n_ro_edi_stock_modified_trailer_1 = fields.Char(string="Modified Trailer 1")
    l10n_ro_edi_stock_modified_trailer_2 = fields.Char(string="Modified Trailer 2")
    l10n_ro_edi_stock_modification_date = fields.Datetime(
        string="Vehicle Modification Date"
    )
