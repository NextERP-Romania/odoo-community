Down payment lines on a sales order, and the down payment lines on the
invoice that follows, normally carry no product. That makes them harder to
report on and to tell apart from the other lines.

This module adds a **Down Payment Product** setting per company. Once it is
set, every new down payment carries that product, on the sales order and on
the invoice.

- One product for all down payments of a company, chosen in the settings.
- Added automatically when a down payment invoice is created; the usual
  **Create Invoice** flow does not change.
- The line description stays the usual *Down Payment* text.
- When the company has no **Down Payment Account** set, the income account
  of the down payment line is taken from the product.
- Set separately for each company in a multi-company database.
