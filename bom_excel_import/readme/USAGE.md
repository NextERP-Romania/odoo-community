# How it works

The wizard drives a fixed four-step flow. Each transition rewrites the
same wizard record and re-opens the form, so the log accumulates as you
progress.

## 1. Upload

Open **Manufacturing → Products → BOM Excel Import**, attach the
`.xlsx` file, optionally adjust **Sheet** and **Start Row**, then
click **Start Import**. The wizard:

- Loads the workbook with `openpyxl` in data-only mode.
- Verifies the sheet exists, otherwise lists the available sheets.
- Moves to the **Operations** step.

## 2. Import operations

Click **Import Operations** to run `action_import_operations`. The
wizard scans every row from the start row downwards and:

- Collects unique workcenter names; missing ones are created in
  `mrp.workcenter`.
- Groups rows by produced product and creates one BOM per product
  (skipping products that already have a BOM).
- Creates one `mrp.routing.workcenter` per distinct operation in the
  group, sequenced in steps of 10 with a 60-minute cycle time.
- Sets the BOM type to `subcontract` and attaches matching partners
  when column 7/8 are filled.

Counters for workcenters, operations and BOMs created are stored on
the wizard and shown on the next screen.

## 3. Import BOM lines

Click **Import BOMs** to run `action_import_boms`. The wizard:

- Re-reads the sheet and groups component rows by produced product.
- Resolves each component via name or internal reference, creating a
  new storable product when nothing matches.
- Resolves the UoM by name; falls back to the component's default UoM
  with a warning.
- Creates one `mrp.bom.line` per component, linked to the right
  operation when column 2 matches. Components already present in the
  BOM are skipped.

## 4. Review the summary

The final screen shows the count of workcenters, operations, BOMs and
BOM lines created, the total error count, and both logs on separate
tabs. Click **Import Another File** to reset the wizard to the upload
step.
