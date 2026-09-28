# Usage

## Hiding the Reverse and Create Invoice buttons on credit notes

Once the module is installed, the **Reverse** and **Create Invoice** action buttons are automatically hidden on `account.move` records that are credit notes (reversal entries). No manual steps are needed — the visibility rules are applied via view inheritance.

### Typical workflow

1. Open **Accounting → Customers → Credit Notes** or **Accounting → Vendors → Refunds**.
2. Open any existing credit note (a move of type `out_refund` or `in_refund`).
3. Notice that the **Reverse** and **Create Invoice** buttons that normally appear in the form header are no longer visible, preventing accidental double-reversal or re-invoicing of a credit note.

The buttons remain fully visible on standard customer invoices and vendor bills, so the normal invoice workflow is unaffected.
