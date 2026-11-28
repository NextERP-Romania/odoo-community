Brings the eTransport improvements of `l10n_ro_edi_stock_extension` to
batch transfers, so a shipment of several transfers declared with a single
notification is filled in and followed exactly like a single transfer.

- **Same checks and data**: values, quantities, weights, customs tariff
  codes and addresses computed as for a transfer.
- **Price source per batch**: cost, purchase order, sale order or sales
  price.
- **Transport documents and previous notifications** on the batch.
- **Post-outage declaration** on the batch.
- **Delete, Confirm transport and Modify vehicle** from the batch, each
  waiting for ANAF's answer.
- **Included in the notifications list synchronization** with ANAF.
- **Protected batches**: a batch whose notification is alive at ANAF
  cannot be deleted or cancelled, and its transfers cannot be added or
  removed by hand.
