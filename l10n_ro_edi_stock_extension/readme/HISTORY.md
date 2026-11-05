# Changelog

## 19.0.1.3.0 (2026-11-05)

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
