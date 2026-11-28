When a customer asks for an invoice for a sale already printed on a fiscal
receipt, the sale and its VAT were already declared with the receipt. The
invoice is then issued for accounting purposes only and must reach
e-Factura with the type code for that case (751), not as a regular
invoice.

- **Fiscal receipt number on the order**: written on the point of sale
  order by the fiscal register integration once the receipt is printed.
- **Carried to the invoice**: an invoice created from the order takes the
  receipt number automatically.
- **Right type code**: an invoice with a receipt number is sent with type
  code 751; every other invoice and every credit note keeps its usual code.
- **Back-office invoices**: the receipt number can be typed on an invoice
  issued later for a receipt printed elsewhere.
- **Locked once sent**: the number can only be changed while the invoice
  is a draft not yet sent to the SPV.
