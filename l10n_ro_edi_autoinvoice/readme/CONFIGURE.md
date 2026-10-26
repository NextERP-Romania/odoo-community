For every customer who issues self-invoices in your name, create a sale journal in **Accounting → Configuration → Journals** with:

| Field | Value |
|---|---|
| **Type** | Sales |
| **Ro Sequence Type** (`l10n_ro_sequence_type`) | Customer Auto Invoicing |
| **Ro Partner** (`l10n_ro_partner_id`) | the customer |

The fields come from the Romanian accounting module (`l10n_ro_account_enterprise`), which this module does not require. Without it, or without a journal for the customer, the self-invoices are created as drafts in the first sale journal.
