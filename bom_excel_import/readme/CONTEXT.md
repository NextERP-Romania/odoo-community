# Key features

- **Multi-step wizard** — a single `bom.excel.import.wizard` transient
  model drives four steps: upload, import operations, import BOM lines
  and a final summary screen.
- **Workcenter auto-creation** — every workcenter name in column 6 that
  is not already present in `mrp.workcenter` is created automatically
  before any operation is linked to it.
- **BOM and operation creation** — for each unique product in column 1
  one `mrp.bom` is created (skipped if a BOM already exists for the
  template) and one `mrp.routing.workcenter` per distinct operation in
  the rows, with a default cycle time of 60 minutes.
- **Subcontracting awareness** — column 7 sets the BOM type to
  `subcontract`, and the comma-separated names in column 8 are matched
  against `res.partner` and attached as subcontractors.
- **Component bootstrapping** — components and produced products are
  searched by name and by `default_code`; if no match is found a new
  storable product is created with the spreadsheet name as default
  code.
- **UoM resolution** — column 4 is matched case-insensitively against
  `uom.uom`; when it cannot be resolved, the component product's
  default UoM is used and a warning is added to the log.
- **Detailed import log** — every row, every created record and every
  error is captured in two text fields (`operations_import_log`,
  `bom_import_log`) shown on the wizard's final tab.
- **External dependency** — relies on the `openpyxl` Python library,
  which must be installed in the Odoo environment.
