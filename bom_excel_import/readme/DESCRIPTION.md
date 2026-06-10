Import Bills of Materials, operations and workcenters from a single Excel
spreadsheet, without touching Odoo's standard data-import tooling. The
module ships a guided wizard that walks through file upload, operations
creation and BOM-line creation, and reports a detailed log for every row.

The expected sheet layout is fixed and column-positional: product
produced, operation name, consumed quantity, component UoM, component,
workcenter, subcontracting flag and a comma-separated list of
subcontractors. Missing workcenters and missing products are created on
the fly (storable goods with the product name as default code) so a
typical first import bootstraps the whole manufacturing master data.

Best suited for teams migrating MRP data from a legacy ERP, prototyping
manufacturing setups from a planning spreadsheet, or maintaining BOMs
externally in Excel and pushing them into Odoo at intervals. Existing
BOMs and components are detected and skipped instead of being
duplicated.
