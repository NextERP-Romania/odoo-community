Sends customer credit notes to ANAF e-Factura as **storno invoices**: an
invoice with negative amounts and a reference to the invoice it reverses,
instead of a credit note with positive amounts. Some companies and their
customers work with storno invoices only; this setting lets them do so.

- **Per company**: enabled only where you choose; other companies keep
  sending regular credit notes.
- **Negative amounts throughout**: quantities, discounts and charges, VAT
  and totals are negative, while the unit price stays positive, as the
  rules require.
- **Linked to the original**: the number and date of the reversed invoice
  are sent with it, so ANAF and the customer can match the two.
- **Matching PDF**: the printed document is titled *Storno Invoice*, shows
  *Invoice Date*, a *Storno of invoice ... dated ...* line and negative
  quantities and amounts.
- **Accounting unchanged**: the credit note and its journal entries stay
  exactly as they are; only the document sent to ANAF and its PDF change.
