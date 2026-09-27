# Changelog

## 20.0.1.4.0 (2026-09-27)

- **The delivery carrier is asked for when the notification is sent, not when
  the transfer is validated.** The base demands one on every incoming and
  outgoing transfer of a Romanian company -- `l10n_ro_edi_stock_enable` is no
  narrower than "not internal, not batched, company in Romania" -- so a shop
  receiving three cartons it fetched itself could not validate its receipt.
  eTransport applies to goods of high fiscal risk above the legal thresholds,
  and the carrier is data the notification needs, so that is where it is now
  demanded, in full: no carrier means one clear error at send time instead of
  three complaints about a transport partner that is not there. Companies that
  declare everything they move keep Odoo's behaviour with **Delivery Carrier
  Required = When the transfer is validated** in the eTransport settings.
- The carrier stays writable on a validated transfer for as long as a
  notification can still be sent for it. Odoo locks the field once the goods
  are done, which made sense only while the carrier had to be there before
  that.

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
