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
    ("available_sub", "Available (sub-location)"),
    ("partial", "Partially available"),
    # Buy route
    ("to_order", "Must be ordered"),
    ("po_draft", "Purchase not validated"),
    ("reception", "Reception needed"),
    # Manufacture route
    ("to_manufacture", "Must be manufactured"),
    ("mo_draft", "Manufacturing not confirmed"),
    ("production", "Production needed"),
    ("mo_late", "Production is late"),
    # Internal transfer route
    ("to_transfer", "Internal transfer needed"),
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
    "reception": 4,
    "production": 4,
    "mo_late": 4,
    "po_draft": 5,
    "mo_draft": 5,
    "to_order": 6,
    "to_manufacture": 6,
    "unavailable": 6,
}
