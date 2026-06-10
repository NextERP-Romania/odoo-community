# Configuration

The module ships with no settings page. All setup is master-data
preparation and access-rights checks.

## 1. Install dependencies

The manifest depends on `stock_account`, so:

- **Inventory** must be installed.
- **Accounting** or another module pulling in `stock_account` must be
  installed so quants carry a `value` and a `standard_price` that the
  inventory lines can snapshot.

## 2. Grant access

The inventory header is editable by `base.group_user`, but both menu
entries are restricted to `stock.group_stock_manager`. Go to
**Settings → Users & Companies → Users** and put the operators who run
inventories in the **Inventory: Administrator** group. Other users can
view inventories only through their record URL.

Access rights for the two new models (read / write / create / unlink)
are defined in `security/ir.model.access.csv` for
`stock.group_stock_user` and `stock.group_stock_manager`.

## 3. Prepare locations

Open **Inventory → Configuration → Warehouses Management → Locations**
and ensure every location that has to be counted is set to **Usage:
Internal**. The inventory form filters location pickers by
`usage == 'internal'` and silently ignores all others.

## 4. Prepare products (optional scoping)

Inventories can be limited to a product list. The form filters the
many2many to products of type `consu` (which in 19.0 covers storable
and non-storable goods). If no product is selected, all internal
locations of the company are scanned.

## 5. Multi-company

`company_id` defaults to `self.env.company` and is propagated through
related fields on the lines. Each company maintains its own
inventories; quants of another company are not picked up when lines
are generated.

## 6. Open the menus

After install the new entries are:

- **Inventory → Operations → Adjustments → Inventory Stock
  Adjustments** — the header list and form (action
  `action_open_stock_inventory`).
- **Inventory → Reporting → Inventory Stock Line Adjustments
  History** — list / pivot / graph over validated lines (action
  `action_open_stock_inventory_line_history`), filtered to
  `state = done` by default.
