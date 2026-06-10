Add a dedicated stock-inventory document on top of `stock.quant` so
physical counts are grouped, dated and valued as a single record. The
module introduces two new models — `l10n.ro.stock.inventory` (the
header) and `l10n.ro.stock.inventory.line` (the counted lines) — with
a form, list and search view, plus a reporting list / pivot / graph
over the lines.

Each inventory is scoped to a set of internal locations and, optionally,
to a list of products. Generating the lines fetches the corresponding
`stock.quant` records, snapshots their on-hand quantity and value, and
lets the operator enter the counted quantity. Validating the inventory
applies the differences through `stock.quant.action_apply_inventory()`
on the chosen accounting date and stores the resulting value
difference per line.

The model also wires the inverse side: when quants are adjusted outside
this workflow (standard Odoo screens, third-party imports), an
`l10n.ro.stock.inventory` is created automatically, grouped by
accounting date, so every stock adjustment ends up captured in a
traceable document.
