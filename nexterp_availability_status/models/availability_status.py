"""Shared taxonomy for the availability traffic-light.

The same set of status codes is reused by stock.move (the source of truth) and
by the documents that aggregate it (stock.picking, mrp.production,
sale.order.line, purchase.order.line). Keeping it in one place guarantees the
OWL widget colours everything consistently.
"""

# code -> default (untranslated) short label. Concrete labels with "in X days"
# are built at compute time; this is the fallback / selection text.
STATUS_SELECTION = [
    ("available", "Available"),
    ("partial", "Partially available"),
    # Buy route
    ("to_order", "Must be ordered"),
    ("po_draft", "Purchase not validated"),
    ("reception", "Reception expected"),
    ("reception_late", "Reception is late"),
    # Manufacture route
    ("to_manufacture", "Must be manufactured"),
    ("mo_draft", "Manufacturing not confirmed"),
    ("mo_unplanned", "Operations not planned"),
    ("mo_planned", "Production expected"),
    ("mo_late", "Production is late"),
    # Internal transfer route
    ("to_transfer", "Internal transfer needed"),
    ("transfer", "Transfer expected"),
    ("transfer_late", "Transfer is late"),
    # Catch-all
    ("unavailable", "Unavailable"),
    ("none", "Not applicable"),
]

# Higher = worse. When rolling several moves up into one document status we keep
# the worst (max) so a document is only as ready as its least-ready line.
STATUS_SEVERITY = {
    "none": -1,
    "available": 0,
    "partial": 1,
    "reception": 2,
    "transfer": 2,
    "mo_planned": 2,
    "po_draft": 3,
    "mo_draft": 3,
    "mo_unplanned": 3,
    "to_transfer": 3,
    "to_order": 4,
    "to_manufacture": 4,
    "reception_late": 5,
    "transfer_late": 5,
    "mo_late": 5,
    "unavailable": 5,
}
