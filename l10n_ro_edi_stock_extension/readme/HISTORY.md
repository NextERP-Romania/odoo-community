# Changelog

## 20.0.1.5.0 (2026-11-06)

- A transfer whose UIT is alive at ANAF (sent, validated, confirmed or with a
  changed vehicle) can no longer be deleted or cancelled; the deletion (DEL)
  has to be sent first. A failed correction does not release it, since ANAF
  still holds the validated notification.
- The deletion, confirmation and vehicle change are refused on the server
  unless ANAF validated the notification (a vehicle change keeps it so) and
  the UIT is the transfer's current one.
- After a vehicle change the Delete, Confirm, Modify vehicle and Amend buttons
  stay available.
- While ANAF processes a notification, the declared eTransport data of the
  transfer, its transport documents and its previous notifications are
  frozen on the server too, not only in the form.
- eTransport documents cannot be deleted from their form either.
- A deletion, confirmation or vehicle change now waits in the new "Action
  Sent" state until its processing status is fetched from ANAF (Fetch Status
  button, or the new, inactive by default, "eTransport: fetch ANAF status of
  transfers" scheduled action), instead of being recorded as done as soon as
  it was uploaded. Accepted: the document moves to Deleted / Confirmed /
  Vehicle Modified (the new vehicle is written on the transfer only then).
  Refused: it moves to Error with ANAF's message and the UIT stays where it
  was, so the transfer stays guarded and the action can be sent again. A
  pending deletion still holds the transfer.
- Uninstalling the module keeps the eTransport documents of these actions:
  confirmations and vehicle changes become Validated (the UIT is still
  valid), deletions and pending actions become Error with their original
  state noted in the message. Before, they were deleted.
- Batch transfers get the same guards: a batch whose UIT is alive at ANAF can
  no longer be deleted or cancelled, and its transfers can no longer be added,
  removed or deleted by hand: the notification declares exactly these goods.
  Odoo's own flows (validation, backorders, cancelling a transfer) still
  detach what they need, and a live batch takes no auto-batched transfer.
  Deletions, confirmations and vehicle changes of a batch notification wait
  for ANAF's processing status like those of a transfer (the new, inactive by
  default, "eTransport: fetch ANAF status of batch transfers" scheduled
  action).

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
