# Configuration

The module ships no setup screen of its own — once installed, a single
menu entry exposes the wizard. Configuration is limited to preparing
the Excel file and making sure the Python dependency is available.

## 1. Install the openpyxl dependency

The wizard refuses to start unless the `openpyxl` library is reachable
from the Odoo server. Install it in the environment used to run Odoo:

```
pip install openpyxl
```

If it is missing, opening the wizard raises a user error pointing back
to this command.

## 2. Prepare the Excel file

The wizard expects a column-positional layout. Header row aside, each
row must use these columns:

| Column | Content |
|---|---|
| 1 | Product produced (name or internal reference) |
| 2 | Operation name |
| 3 | Quantity consumed |
| 4 | Component UoM (matched against `uom.uom` by name) |
| 5 | Component (name or internal reference) |
| 6 | Workcenter name |
| 7 | Subcontracting flag (truthy value sets BOM type to `subcontract`) |
| 8 | Subcontractors, comma-separated partner names |

By default the wizard reads the sheet named `Sheet1` and starts at row
`2` (one header row). Both values are editable on the upload screen.

## 3. Open the wizard

Go to **Manufacturing → Products → BOM Excel Import**. The wizard
opens on the upload step.

## 4. User access

The wizard is exposed via `bom.excel.import.wizard` with read/write
access for `mrp.group_mrp_user` (see `security/ir.model.access.csv`).
Any Manufacturing user can run the import; component and product
creation happens through the same user.

## 5. Optional sheet/start-row override

If the spreadsheet does not follow the default layout:

1. Fill in **Sheet** with the actual sheet name (must exist in the
   workbook, otherwise the wizard lists available sheets in the error
   message).
2. Set **Start Row** to the first data row (e.g. `1` if there is no
   header).
