# Changelog

## 20.0.1.3.0 (2026-09-26)

- Merge `l10n_ro_edi_stock_batch_extension` into this module, mirroring Odoo
  20.0, where `l10n_ro_edi_stock_batch` was merged into `l10n_ro_edi_stock`
  (`stock_picking_batch` itself became part of `stock`). Batch transfer support
  is unchanged functionally. A pre-migration script merges the old module into
  this one with `openupgradelib` (`update_module_names(..., merge_modules=True)`),
  so its records change owner instead of being dropped, and a post-migration
  script uninstalls the old module should the merge not have run.

## 19.0.1.2.0 (2026-09-15)

- Drop the base `Warehouse of ... should be in Romania` error on the
  counterparty side of intra-EU / import / export operations, which
  `l10n_ro_edi_stock` started raising unconditionally and which made those
  notifications impossible to send.
- Fix `AttributeError` when the ANAF response has an unexpected shape:
  `ETransportAPI` is a plain class, so the module-level `_` has to be used
  instead of `self.env._`.
- `_compute_l10n_ro_edi_stock_enable_send` now only widens the states the base
  does not already cover ('assigned' has been allowed upstream since 19.0).

## 19.0.1.0.0 (2026-06-23)

- _Changelog tracking starts at this release._
