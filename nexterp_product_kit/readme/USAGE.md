# Daily use

## Pricing behaviour

Once a product has at least one entry in the **Kit Products** tab,
its price stops behaving like a regular product:

- **Sales Price (`lst_price`)** is recomputed as
  `sum(line.product_qty * component.lst_price)` for every kit line.
  Changing a component's list price flows through to the kit price
  immediately.
- **Cost (`standard_price`)** is aggregated the same way from each
  component's cost.
- When a **pricelist** is active in the context, the kit price is
  rebuilt by calling the pricelist on each component (using the
  component's own UoM, the requested quantity, the partner and the
  date) and summing the results, instead of using the kit's flat
  list price.

## Editing a kit

To change what a kit contains, open the kit product and edit the
lines in the **Kit Products** tab — add, remove or adjust quantities.
The kit's price refreshes the next time prices are computed (form
re-open, pricelist evaluation, report rendering, etc.).

## Browsing kits

Use **Sales → Products → Product Kits** to see every component line
across the database. The pivot view groups by category, template
and product on rows and by component on columns, and measures
**Quantity** and **Price**, which is useful for auditing kits that
share the same components or for spotting outliers in component
quantities.

## Behaviour on dependent modules

This module only defines the kit data and the price aggregation. To
explode kit lines onto sale orders, install
`nexterp_product_kit_sale`. To create one task per service component
on confirmation, add `nexterp_product_kit_sale_timesheet` on top.
