# Changelog

## 19.0.1.3.0 (2026-11-05)

- A batch whose UIT is alive at ANAF can no longer be deleted or cancelled,
  and its transfers can no longer be added, removed or deleted by hand: the
  notification declares exactly these goods. Odoo's own flows (validation,
  backorders, cancelling a transfer) still detach what they need, and a live
  batch takes no auto-batched transfer.
- The deletion, confirmation and vehicle change of a batch notification are
  refused on the server unless ANAF validated it; after a vehicle change the
  buttons and the amendment stay available.
- While ANAF processes the batch notification its eTransport data, transport
  documents and previous notifications are frozen on the server too.
- Deletions, confirmations and vehicle changes of a batch notification wait
  for ANAF's processing status like those of a transfer (Fetch Status button,
  or the new, inactive by default, "eTransport: fetch ANAF status of batch
  transfers" scheduled action); a pending or refused deletion keeps the
  batch guarded.

## 19.0.1.2.0 (2026-09-15)

- Keep a picking sendable to eTransport while its batch is still in progress
  and has not been notified itself. `l10n_ro_edi_stock_batch` disables
  eTransport on every picking belonging to a batch, which defeated sending the
  notification before the goods move.

## 19.0.1.0.0 (2026-06-23)

- _Changelog tracking starts at this release._
