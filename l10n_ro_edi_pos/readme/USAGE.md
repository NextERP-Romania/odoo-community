# Usage

## Flow 1 — Invoice generated automatically from a POS order

1. The cashier completes the sale in Point of Sale. The fiscal register prints the receipt and its driver writes the receipt number into the **Fiscal Receipt Number** field on the `pos.order`.
2. When the customer requests an invoice, generate it from the POS order in the usual way (*Point of Sale → Orders → Orders* → open the order → **Create Invoice**).
3. Odoo copies the receipt number into the invoice's `l10n_ro_fiscal_receipt_number` field automatically (computed from the linked POS orders).
4. Send the invoice to ANAF via *Accounting → Customers → Invoices* → open the invoice → **Send & Print** (or the e-Factura action). The UBL-RO XML is exported with type code **751** instead of the usual 380.

## Flow 2 — Back-office invoice for a receipt issued outside Odoo

1. Go to *Accounting → Customers → Invoices* and create or open a draft invoice.
2. Open the **Other Info** tab and fill in **Fiscal Receipt Number** (`l10n_ro_fiscal_receipt_number`) with the number printed on the fiscal receipt.
3. Confirm the invoice while it is still a draft (the field becomes read-only once the invoice has been sent to the SPV).
4. Send to ANAF. The XML is exported with type code **751**.

> **Note:** Invoices without a fiscal receipt number, and all credit notes, are exported with their standard type code (380 / 381). A POS terminal configured to sell on invoice only (no fiscal register) produces no receipt number; its invoices remain 380.
