# Daily use

Once configured, the module is fully transparent — there is no extra
report action or menu. Every invoice or refund printed from the
standard **Print -> Invoice** action on `account.move` uses the
inherited template.

## Printing an invoice

1. Open a confirmed invoice from **Accounting -> Customers ->
   Invoices** (or **Vendors -> Bills**).
2. Click **Print -> Invoice**.
3. The generated PDF includes the extra **VAT** and/or **Total**
   columns if the corresponding company options are enabled.

## Printing a refund (storno)

1. Open a posted **Credit Note** (`out_refund`) or vendor **Refund**
   (`in_refund`).
2. Click **Print -> Invoice**.
3. If **Print Show Refunds** is enabled on the company, all numeric
   values on the PDF — line quantities, base amounts, tax amounts,
   totals and section subtotals — are rendered with a minus sign.

## How it works

- `_compute_tax_totals` on `account.move` inverts the sign of every
  `base_amount`, `tax_amount` and `total_amount` (and their currency
  counterparts) on refund moves whose company has *Print Show Refunds*
  enabled.
- Line, section and grouped-line helpers (`get_section_subtotal`,
  `get_section_tax_amount`, `get_section_total_amount`,
  `_get_child_lines`) apply the same sign so subtotals stay consistent
  with the per-line numbers.
- Each quantity span uses the UoM's `report_precision` when *Print
  Invoice Tax Value* is on, so a kilogram line with precision `3`
  prints as `1,250` instead of `1,25`.
