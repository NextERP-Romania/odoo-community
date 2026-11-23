# Key features

- **Automatic ingestion of *autofacturi*** — self-invoices customers upload to the SPV in your company's name are taken in as customer invoices, not vendor bills.
- **Reliable XML recognition** — a document is treated as a self-invoice only when the supplier VAT matches your company and the UBL type code is 389, so your own outgoing invoices are never confused with one.
- **Dedicated self-invoicing journals** — set `l10n_ro_sequence_type` to *Customer Auto Invoicing* and `l10n_ro_partner_id` to the customer; the imported invoice keeps the customer's own number and is posted automatically.
- **SPV deduplication** — an imported self-invoice is immediately flagged as validated in the SPV so a later synchronization never creates a duplicate.
- **Both SPV sync paths covered** — works with the `l10n_ro_edi` scheduled sync and with the **SPV Messages** list from `l10n_ro_message_spv` (ticked *Self-Invoice* → *Create Invoice*).
- **Outbound *autofacturi* handled too** — vendor bills/refunds on a *Supplier Auto Invoicing* purchase journal are uploaded to ANAF with `autofactura=DA`, `standard=UBL` (or `CN` for credit notes), and `CreditNoteTypeCode` 381 instead of Odoo's default 261.
- **Company-level toggle** — `l10n_ro_create_customer_autoinvoice` in **Settings → Accounting** controls whether self-invoices are taken in as customer invoices at all.
- **No enterprise dependency** — the *Ro Auto Invoicing* journal fields are added by this module itself; `l10n_ro_account_enterprise` is optional.
