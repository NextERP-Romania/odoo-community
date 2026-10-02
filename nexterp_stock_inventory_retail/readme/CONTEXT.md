# Key features

- **Markup and deferred VAT per line** —
  `l10n_ro_retail_markup_value` (378) and `l10n_ro_retail_vat_value`
  (4428) are filled on `l10n.ro.stock.inventory.line` at the same
  moments as the cost difference, through the `_update_diff_values`
  hook of the base module.
- **Retail value of the difference** — `l10n_ro_retail_value` adds the
  cost difference, the markup and the deferred VAT: the amount account
  371 moves by.
- **Shelf price on the line** — `l10n_ro_retail_price` shows the PVA
  the shop currently charges, read once per warehouse through
  `product._l10n_ro_get_retail_prices_batch()`.
- **Valued the way it will be booked** — a surplus is loaded from the
  retail pricelist of the shop, a shortage released from
  `l10n.ro.retail.markup.line` at the *coeficient de repartizare a
  adaosului comercial*, mirroring
  `stock.move._l10n_ro_retail_in_amounts()` /
  `_l10n_ro_retail_out_amounts()`.
- **Document drawn at the PVA** — `_report_diff_value()` returns the
  retail value for a line held in a shop, so the per-location summary,
  the differences and their totals of the printed report are stated at
  shelf price, and the unit price column with them.
- **Report section** — the report gains a *Differences at shelf price*
  table (difference, shelf price, cost, markup, deferred VAT, retail
  value) breaking down the amounts above, for the lines held in a
  retail location.
- **Header totals** — `l10n_ro_retail_markup_value`,
  `l10n_ro_retail_vat_value` and `l10n_ro_retail_value` on the
  inventory, next to the cost totals of the base module.
- **Auto-installed** — the module installs by itself as soon as both
  `nexterp_stock_inventory` and `l10n_ro_stock_account_retail` are
  present.
