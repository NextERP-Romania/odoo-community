# Daily use

The Certificate of Conformity is intended to be printed together with
the delivery slip whenever goods leave the warehouse and the customer
requires a sanitary / food-safety declaration.

## Printing the certificate

1. Open a delivery from **Inventory -> Operations -> Transfers** (or
   from the sale order's *Delivery* smart button).
2. Validate the picking so it reaches the **Done** state — the report
   body only renders for `state == 'done'`.
3. From the picking form, click **Print -> Conformity Report**.
4. Odoo generates a PDF named `Conformity_Report - <picking name>.pdf`
   and downloads it. The file can be attached to the delivery or sent
   to the customer.

## What appears on the PDF

- **Header**: customer address, VAT, trade register.
- **Title block**: *Certificate of Conformity*, picking series /
  number, dispatch date, order number (sale order or customer
  reference).
- **Move-line table**: one row per move line, with row number,
  product, customer product code, lot number, UoM, quantity done and
  lot expiration date.
- **Declaration**: the issuing company guarantees that the listed
  products do not endanger life or health and comply with the sanitary
  / veterinary food-safety legislation in force.
- **Signature block**: agent, supplier code and sale order on the
  left; shipping information, delegate name, ID, means of transport,
  date / hour and signature lines on the right.

## Language

The report is rendered with `lang = company.partner_id.lang`, so the
certificate language follows the company's own configured language
(useful when the customer language differs from the company language).
