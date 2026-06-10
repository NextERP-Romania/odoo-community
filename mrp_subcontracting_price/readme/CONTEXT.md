# Key features

- **Purchase-driven valuation** — the override of `stock.move._get_value_data`
  returns the origin move's value when the incoming move
  `is_subcontract`, both legs are `done`, and `move_orig_ids` exists.
  The standard Odoo computation is bypassed in that case.
- **Automatic re-trigger on done** — `stock.move._action_done` is
  extended so any inbound move with subcontracting destinations runs
  `_set_value()` on its `move_dest_ids` after standard processing,
  ensuring the new valuation rule is applied at the right moment.
- **Single inheritance, no new models** — the module adds no fields,
  views, menus or wizards; only two methods are overridden on
  `stock.move`.
- **Romanian-stock-account integration** — the manifest depends on
  `l10n_ro_stock_account`, so the value flow uses the Romanian
  inventory-valuation logic (separate goods received / not invoiced
  account, FIFO/AVG per location, etc.).
- **Subcontracting-purchase integration** — depends on
  `mrp_subcontracting_purchase`, the Odoo bridge that links a
  subcontracting BOM to the purchase order line, providing the
  `is_subcontract` flag and the move chain the override walks.
- **Origin-move tracing** — uses Odoo's
  `_get_value_from_origin_move(quantity)` helper to fetch the value
  proportional to the received quantity, so partial subcontract
  receipts are valued correctly.
- **No effect when components are valued at receipt** — the override
  only triggers for subcontract moves with an origin chain; regular
  moves keep the standard Odoo costing.
