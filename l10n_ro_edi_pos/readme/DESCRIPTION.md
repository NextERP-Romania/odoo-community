When a customer asks for an invoice for a sale already on a fiscal receipt,
the sale and its VAT were declared with the receipt; the invoice is issued
for accounting purposes only and goes to RO e-Factura with type code
**751** ("Factură — informații în scopuri contabile") instead of 380.

The module adds the **Fiscal Receipt Number** to the point of sale order,
written by the register's driver once the receipt is printed, and to the
invoice, filled from the orders behind it. An invoice with a receipt number
is exported as 751; any other invoice, and every credit note, keeps its
usual type code. A point of sale without a register, or one that sells on
invoice only, prints no receipt: its invoices stay 380.
