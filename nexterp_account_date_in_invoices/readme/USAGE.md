# Usage

This module works automatically in the background — no additional steps are required from the user during day-to-day invoicing.

## How the accounting date is determined on vendor bills

Whenever Odoo computes the accounting date for a purchase invoice (`account.move`), the overridden `_get_accounting_date` method applies the following logic:

1. Open or create a vendor bill via **Accounting → Vendors → Bills**.
2. Set the **Invoice Date** field on the bill.
3. On confirmation, Odoo automatically sets the **Accounting Date**:
   - If the invoice date falls **after** the current `tax_lock_date`, the accounting date is set to the **invoice date**.
   - If the invoice date falls **on or before** the `tax_lock_date`, the accounting date is pushed forward to **tax lock date + 1 day**, keeping the entry out of the locked fiscal period.
4. No manual intervention is needed — the correct accounting date appears on the posted journal entry.
