## 19.0.1.1.0 (2026-11-05)

- A self-invoice taken in from the SPV and left in draft (no self-invoicing
  journal for the customer) can no longer be deleted, and it can only be
  posted in a Customer Auto Invoicing journal, where it takes the customer's
  number; it is never numbered in one of our own sequences.
- The self-invoicing type and partner of a journal are locked once the journal
  has posted entries.

## 19.0.1.0.0 (2026-10-26)

- First version: self-invoices issued by customers in the company's name, taken in from the SPV as customer invoices, with the self-invoicing fields on sale and purchase journals; the self-invoices issued in a supplier's name are uploaded with `autofactura=DA` (moved from `account_invoice_delivery_sheet`) and their credit notes carry `CreditNoteTypeCode` 381 (moved from `l10n_ro_edi_extension`).
