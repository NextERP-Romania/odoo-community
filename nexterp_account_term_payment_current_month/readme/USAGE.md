# Usage

## Using a "Current Month" Payment Term on an Invoice

1. Open **Accounting → Customers → Invoices** (or **Vendors → Bills**).
2. Select or create a document and locate the **Payment Terms** field.
3. Choose a payment term that was configured with the *Current Month* delay type (see CONFIGURE).
4. Confirm the invoice. The **Due Date** field is automatically calculated so that it falls at the end of the current calendar month (or the configured number of days within the current month), rather than counting days from the invoice date.

## Verifying the computed due date

- After selecting the payment term, Odoo recalculates and displays the **Due Date** immediately in the invoice header.
- For payment terms that split the balance into multiple lines, each line's due date is shown in the **Payment term** breakdown pop-up (click the ℹ icon next to the due date).
