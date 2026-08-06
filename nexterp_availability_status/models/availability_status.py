"""Shared taxonomy for the availability traffic-light.

The same set of status codes is reused by stock.move (the source of truth) and
by the documents that aggregate it (stock.picking, mrp.production,
sale.order.line, purchase.order.line). Keeping it in one place guarantees the
OWL widget colours everything consistently.
"""

STATUS_SELECTION = [
    ("available", "Available"),
    ("available_sub", "Available (sub-location)"),
    ("partial", "Partially available"),
    # From the reservation chain (move_orig_ids)
    ("reception", "Reception needed"),
    ("production", "Manufacturing needed"),
    ("to_transfer", "Transfer needed"),
    ("po_draft", "Purchase not confirmed"),
    ("mo_draft", "Manufacturing not confirmed"),
    # No chain
    ("must_transfer", "Must be transfered"),
    ("to_manufacture", "Must be manufactured"),
    ("to_order", "Must be ordered"),
    # Catch-all
    ("unavailable", "Unavailable"),
    ("none", "Not applicable"),
]

# Higher = worse. When rolling several moves up into one document status we keep
# the worst (max) so a document is only as ready as its least-ready line.
STATUS_SEVERITY = {
    "none": -1,
    "available": 0,
    "available_sub": 1,
    "partial": 2,
    "to_transfer": 3,
    "reception": 3,
    "production": 3,
    "must_transfer": 4,
    "po_draft": 5,
    "mo_draft": 5,
    "to_order": 6,
    "to_manufacture": 6,
    "unavailable": 6,
}
