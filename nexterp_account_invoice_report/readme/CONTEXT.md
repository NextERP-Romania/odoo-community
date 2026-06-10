# Key features

- Inherits `account.report_invoice_document` (priority 100) so the
  standard Invoice / Credit Note PDF is replaced everywhere it is used.
- Optional **VAT** column added next to each invoice line, showing
  `price_total - price_subtotal` per line.
- Optional **Total** column added next to each invoice line, showing
  the line total including taxes.
- Refund (storno) invoices can be printed with negative quantities,
  base, tax and total amounts so that the document visually matches the
  accounting sign.
- Section subtotals on grouped layouts are recomputed via
  `get_section_subtotal`, `get_section_tax_amount` and
  `get_section_total_amount` to remain consistent with the printed sign.
- New `report_precision` field on `uom.uom` lets each unit of measure
  define its own number of decimal places for printed quantities.
- The grouped lines view (`td_quantity_grouped`) is patched so the unit
  count column also respects the refund sign and UoM precision.
- All toggles are per company, stored on `res.company`, and exposed
  through the standard Accounting Settings form.
