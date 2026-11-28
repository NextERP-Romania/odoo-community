When an invoice is created by mistake, Odoo keeps its number taken even
after the invoice is deleted, leaving a gap in the sequence. This module lets
a company give the number back: if the deleted invoice is the last one issued
in its journal, the next invoice reuses its number and the sequence stays
continuous.

- **Allow Delete Last Invoice** option, set per company in the invoicing
  settings.
- Only the most recent invoice of a journal can release its number; earlier
  invoices keep the standard protection.
- Off by default: nothing changes for a company until the option is ticked.
- Works for customer invoices, vendor bills, credit notes and other journal
  entries numbered by a journal sequence.
