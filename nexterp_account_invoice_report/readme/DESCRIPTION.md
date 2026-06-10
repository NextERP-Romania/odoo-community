`nexterp_account_invoice_report` extends the standard Odoo customer invoice
PDF to better match Romanian accounting practice. It inherits the
`account.report_invoice_document` QWeb template and adds two optional
per-line columns (VAT amount and total amount) plus the option to print
refund invoices with explicit negative quantities and amounts.

The behaviour is driven by three company-level switches exposed under
Accounting Settings. When enabled, the report displays refund (storno)
quantities, base, tax and totals with a minus sign and renders the
extra columns on both detailed and grouped invoice layouts. Section
subtotals are recomputed accordingly through helper methods on
`account.move.line`.

A complementary `report_precision` field is added on `uom.uom`, so each
unit of measure can override how many decimal places are printed for
quantities on the invoice — useful for products sold in kilograms,
litres or meters where the standard Product Unit precision is not
granular enough.
