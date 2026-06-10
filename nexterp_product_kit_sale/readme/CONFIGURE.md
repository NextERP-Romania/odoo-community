# Configuration

There is no dedicated configuration screen — the module activates
itself as soon as kit data exists on the products you sell.

## 1. Prepare the kit catalog

1. Configure the kit product and its components in the base module:
   - Tick **Is a Kit Component** on each component at **Sales →
     Products → Products**.
   - Open the kit product and fill the **Kit Products** tab.
   See the `nexterp_product_kit` documentation for the full setup.

## 2. Pricelist and taxes

1. Make sure each component product has the correct entries in any
   **Sales → Configuration → Pricelists** that you use, because the
   explosion prices each kit line through the order's pricelist (not
   from the parent SO line).
2. Set taxes (`tax_ids`) on the kit product as usual — the parent SO
   line copies them to every generated kit line.

## 3. Access rights

The `sale.order.line.kit` model is delivered with its own
`ir.model.access.csv` entry. Users who already have access to sale
orders (Salesperson / Sales Manager) automatically see and edit the
**Kit Order Lines** tab.

## 4. Sale order form

No further configuration is needed. The **Kit Order Lines** tab is
appended automatically to the standard sale order form
(`sale.view_order_form`). The tab is grouped by parent SO line and
becomes read-only once the order is cancelled or locked.
