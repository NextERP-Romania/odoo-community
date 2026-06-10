# Configuration

All options are per company and are exposed in the standard Inventory
settings page, right after the *Operations* block.

## 1. Enable the print options

1. Go to **Inventory -> Configuration -> Settings**.
2. Scroll down past the **Operations** block.
3. Tick the options you want enabled for the printed delivery slip:
   - **Delivery slip report only name** — print only the product name,
     hide the `[internal reference] Name` prefix and the picking
     description.
   - **Delivery slip report uom precision** — format quantities using
     the per-UoM **Report Precision**.
   - **Picking report lang company** — print receipts and internal
     transfers in the company partner's language.
4. **Save** the settings. Repeat per company in a multi-company
   database.

## 2. Set UoM print precision

This module relies on the `report_precision` field added on `uom.uom`
by **nexterp_account_invoice_report**.

1. Go to **Inventory -> Configuration -> Units of Measure -> Units of
   Measure**.
2. Open a unit (e.g. *kg*, *l*, *m*) and set **Report Precision** to
   the number of decimal places you want printed on delivery slips.
3. Leave the field empty (or `0`) to keep the default behaviour for
   that UoM.

## 3. Language of receipts

When **Picking report lang company** is on, only receipts and internal
transfers switch to the company language; customer deliveries
(`picking_type_code == 'outgoing'`) keep the standard language
resolution and print in the customer's language.
