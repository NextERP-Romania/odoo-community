# Key features

- **New "Current Month" delay type** added to `account.payment.term.line`,
  complementing Odoo's built-in *Days*, *End of Month* and *End of Next Month* options.
- **Automatic due-date calculation** anchored to the current calendar month,
  so due dates never spill into the following month unexpectedly.
- **Drop-in extension** — inherits `account.payment.term` and
  `account.payment.term.line` with no breaking changes to existing terms.
- **Works across all accounting documents** — customer invoices, vendor bills,
  credit notes and payment schedules all respect the new delay type.
- **No extra configuration required** — install the module and the new
  delay type appears immediately in the Payment Terms configuration UI.
