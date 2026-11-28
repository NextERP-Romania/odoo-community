Self-invoices that your customers issue in your company's name and upload
to the SPV are taken in as customer invoices, not as vendor bills. The
customer uploads them, but they show your company as supplier: they are
your sales.

The module also handles the other direction. When you issue self-invoices
in a supplier's name, they are sent to ANAF in the form ANAF accepts.

- **Reliable recognition**: a document counts as a self-invoice only when
  your company is the supplier and the document is marked as self-billed,
  so your own invoices are never mistaken for one.
- **The customer's number is kept**: in a self-invoicing journal set up for
  that customer, the invoice keeps the number the customer gave it and is
  posted automatically.
- **No duplicates**: the invoice is marked as validated in the SPV, so a
  later synchronization does not create it again and it is never sent back
  to ANAF.
- **Both synchronizations covered**: the scheduled e-Factura download and
  the **Messages SPV** list.
- **Outgoing self-invoices**: vendor bills and refunds on a supplier
  self-invoicing journal are uploaded as self-invoices, and their credit
  notes carry the type code CIUS-RO accepts.
- **Protected drafts**: a self-invoice left in draft cannot be deleted and
  can only be posted in a customer self-invoicing journal.
