# Key features

- **Inventory header model** — `l10n.ro.stock.inventory` ties an
  accounting date, a company, internal locations and (optionally) a
  product list to a draft/done state, with an auto-computed name like
  `Inventory - YYYY-MM-DD`.
- **Counted-line model** — `l10n.ro.stock.inventory.line` carries the
  counted quantity, on-hand quantity, difference, standard price,
  current value, post-validation value and value difference, each
  line linked to a `stock.quant`.
- **Quant uniqueness** — a Postgres constraint
  `unique(inventory_id, quant_id)` blocks the same quant from
  appearing twice on the same inventory.
- **Generate / clear actions** — `Generate Inventory Lines` fetches
  quants for the configured locations and products (creates missing
  quants on the fly), `Clear Inventory Lines` removes them and resets
  the flag.
- **Validate action** — `Validate Inventory` calls
  `stock.quant.action_apply_inventory()` on each line with the
  inventory's accounting date, snapshots the new value, computes the
  per-line value difference and locks the document.
- **Reverse capture** — the override of
  `stock.quant.action_apply_inventory` creates one
  `l10n.ro.stock.inventory` per accounting date when quants are
  adjusted outside this workflow, so manual quant edits are still
  archived as inventory documents.
- **Reporting** — a list / pivot / graph view on
  `l10n.ro.stock.inventory.line` filterable by inventory, product,
  lot, location and accounting date, with `quantity`,
  `inventory_quantity` and `inventory_diff_quantity` as measures.
- **Manager-only menus** — both menus live under the existing
  `stock.menu_stock_adjustments` / `stock.menu_warehouse_report`
  parents with `groups="stock.group_stock_manager"`.
