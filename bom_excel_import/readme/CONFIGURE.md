1. Make sure the `openpyxl` Python library is installed on the server
   running Odoo; the wizard tells you if it is missing.
2. Users need the **Manufacturing / User** access right to run the import.
3. Prepare the Excel file with one header row and these columns, in this
   order:

   | Column | Content |
   |---|---|
   | 1 | Product produced (name or internal reference) |
   | 2 | Operation name |
   | 3 | Quantity consumed |
   | 4 | Component unit of measure (by name) |
   | 5 | Component (name or internal reference) |
   | 6 | Work center name |
   | 7 | Subcontracting flag (any value marks the bill of materials as subcontracted) |
   | 8 | Subcontractors, comma-separated partner names |

By default the wizard reads the sheet named *Sheet1* from row 2; both can be
changed on the upload screen.
