# Usage

This module extends the existing eTransport workflows on batch transfers. The steps below assume `l10n_ro_edi_stock_batch` and `l10n_ro_edi_stock_extension` are already in use for individual transfers.

## Sending an eTransport notification from a batch transfer

1. Navigate to **Inventory → Operations → Batch Transfers** and open (or create) the batch you want to declare.
2. On the batch form, locate the **eTransport** section (added by this module).
3. Set **eTransport Price Source** (`l10n_ro_edi_stock_price_source`) to the value appropriate for the shipment — e.g. *Purchase order price* for inbound goods.
4. If the transport is a continuation or correction of a previous notification (operations 60/70), add entries under **Previous Notifications** (`l10n_ro_edi_stock_previous_ids`).
5. Add any accompanying **Transport Documents** (`l10n_ro_edi_stock_document_line_ids`) (CMR, waybill, etc.).
6. If the notification could not be sent during an ANAF outage, tick **Post-Outage Declaration** (`l10n_ro_edi_stock_post_outage`).
7. Click the **Send eTransport** button (from the action wizard). The wizard (`l10n.ro.edi.stock.action.wizard`) validates the batch data against ANAF Schematron v2.0.2 and uploads the XML. The returned UIT is stored on the batch.

## Modifying vehicle or deleting/confirming a previously sent notification

1. Open the batch transfer that already has a UIT.
2. Use the **Delete**, **Confirm**, or **Modify Vehicle** actions available on the batch form (same wizard, `batch_id`-aware branch).
3. ANAF's response is logged on the chatter.

## Monitoring batch UITs via the ANAF LIST cron

The scheduled action **eTransport — ANAF LIST sync** (defined in `l10n_ro_edi_stock`) automatically reconciles batch UITs alongside individual transfer UITs. No extra configuration is needed — batches are included in `_l10n_ro_edi_stock_list_sync_one` automatically.
