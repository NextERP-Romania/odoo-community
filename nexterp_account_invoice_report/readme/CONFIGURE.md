# Configuration

All options are configured per company under
**Accounting -> Configuration -> Settings**, in the
**Account invoice report options** block (added right after the
standard *Account Reports* block).

## 1. Enable the print options

1. Go to **Accounting -> Configuration -> Settings**.
2. Scroll to the **Account invoice report options** block.
3. Tick any of the following options, depending on what you need on the
   printed invoice:
   - **Print Show Refunds** — print refund / storno invoices with
     negative quantities, base, taxes and totals.
   - **Print Invoice Tax Value** — add a per-line **VAT** column.
   - **Print Invoice Total Value** — add a per-line **Total** column.
4. **Save** the settings. The options are stored on the current
   company; in a multi-company database, switch company and repeat the
   configuration if needed.

## 2. Set per-UoM print precision (optional)

The module also adds a **Report Precision** field on units of measure.

1. Go to **Inventory -> Configuration -> Units of Measure -> Units of
   Measure**.
2. Open a unit (e.g. *kg*, *l*, *m*) and set **Report Precision** to
   the number of decimal places you want printed on invoices for that
   UoM. Leave at `0` to fall back to the default behaviour.

No other setup is required — the inherited invoice template is used
automatically by the standard *Invoice* print action on
`account.move`.
