# Usage

## Deleting the last invoice in a journal

Once the `account_allow_delete_last_invoice` setting is enabled for your company (see **Configure**), users with the appropriate access rights can delete the most recent posted invoice in a journal directly from the standard invoice list or form.

1. Go to **Invoicing → Customers → Invoices** (or **Vendor Bills** for supplier invoices).
2. Open the invoice you want to delete — it must be the last posted entry in its journal sequence.
3. Reset the invoice to draft if required, then use the **Action → Delete** option (or the delete button in the list view).
4. Odoo will allow the deletion instead of raising the usual sequence-lock error, because the `unlink` method on `account.move` has been extended to respect the company-level `account_allow_delete_last_invoice` flag.

> **Note:** Only the *last* invoice in the journal sequence can be deleted this way. Earlier entries remain protected to preserve accounting sequence integrity.
