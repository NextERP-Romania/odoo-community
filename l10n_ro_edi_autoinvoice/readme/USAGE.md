## Self-invoices received from customers

1. Nothing to do by hand: the scheduled e-Factura synchronization creates
   the self-invoices directly as customer invoices.
2. In **Invoicing > Accounting > SPV > Messages SPV** they are ticked
   **Self-Invoice**; **Create Invoice** creates them the same way.
3. Open **Invoicing > Customers > Invoices**. A self-invoice posted in the
   customer's journal carries the customer's number.
4. A self-invoice left in draft explains why in its chatter: no journal for
   that customer, or the error that stopped the posting. Create the
   journal, set it on the invoice and confirm.

## Self-invoices issued in a supplier's name

1. Create the vendor bill or refund on the supplier's *Supplier Auto
   Invoicing* journal and confirm it.
2. Send it to ANAF like any invoice, with **Send & Print** or by the
   scheduled sending. It is uploaded as a self-invoice, and ANAF's answer
   is kept in the chatter.
