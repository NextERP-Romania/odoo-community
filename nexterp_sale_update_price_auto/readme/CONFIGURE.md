# Configuration

The behaviour is opt-in per company through a single setting in the
Sales configuration form.

## 1. Enable the automatic recomputation

1. Go to **Sales -> Configuration -> Settings**.
2. Find the **Pricelists** block.
3. Tick **Auto Update Sales Prices** (added by the module immediately
   after the standard `pricelist_configuration` setting).
4. Click **Save**.

The option is stored on `res.company.sale_auto_update_price` and the
field on `res.config.settings` is `related` (so the value is read
from / written to the current company directly).

## 2. Multi-company

In a multi-company database, repeat the procedure for every company
that should benefit from the automatic recomputation. Companies where
the setting is left off keep the standard Odoo behaviour — changing
the pricelist still shows the **Update Prices** banner that has to be
clicked by the salesperson.

## 3. Prerequisites

- The module requires only `sale_management` and works with both the
  product pricelist engine and the discount / formula rules already in
  Odoo.
- For the automatic recomputation to make sense, make sure the
  relevant pricelists are properly configured under
  **Sales -> Products -> Pricelists** (or **Sales -> Configuration ->
  Pricelists**) and that they cover the customers' products and
  currencies.

No menu, action or scheduled job is added by this module.
