Adds a payment term rule that sets the due date on a fixed day of the month
in which the invoice is issued, for example *on the 25th of the same month*.

- New delay type **Day of the current Month** on payment term lines.
- The due date is that day of the invoice's month, whatever the invoice date.
- Can be combined with other lines, for example part on the 15th and the
  balance on the last working days.
- Payment term lines using the rule fall back to the standard delay type if
  the module is uninstalled.
