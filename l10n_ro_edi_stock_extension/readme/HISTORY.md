## 20.0.1.6.1

- Apps listing: English description, configuration and usage, new icon and cover.

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
  outgoing transfer of a Romanian company, so a shop
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

- Batch transfer support, previously a separate module, is now part of
  this one; the separate module is merged in automatically on update, with
  no change in behaviour.

## 19.0.1.2.0 (2026-09-15)

- Notifications for intra-EU, import and export operations can be sent
  again: the check that the counterparty's warehouse is in Romania no longer
  blocks them.
- An unexpected answer from ANAF is reported as a clear error instead of
  stopping the operation.
- A transfer can be sent to eTransport in every state where it makes
  sense, not only in the states the base localization allowed.

## 19.0.1.0.0 (2026-06-23)

- _Changelog tracking starts at this release._
