For every customer who issues self-invoices in your name, create a sale journal in **Accounting → Configuration → Journals** with:

| Field | Value |
|---|---|
| **Type** | Sales |
| **Ro Sequence Type** (`l10n_ro_sequence_type`) | Customer Auto Invoicing |
| **Ro Partner** (`l10n_ro_partner_id`) | the customer |

For the self-invoices you issue in a supplier's name, the purchase journal works the same way, with **Supplier Auto Invoicing** and the supplier as **Ro Partner**.

The fields are in the **Ro Auto Invoicing** group of the journal form, on sale and purchase journals. The module adds them itself, so `l10n_ro_account_enterprise` is not needed; when it is installed, its own group shows them instead. Without a journal for the customer, its self-invoices are created as drafts in the first sale journal.
