# Daily use

## Adding a kit to a quotation

1. Open **Sales → Orders → Quotations** and create a quotation.
2. On the **Order Lines** tab, add a line with a kit product (any
   product that has entries in its **Kit Products** tab).
3. Save the order. The module reads `product.product.kit` and
   automatically creates one `sale.order.line.kit` per component
   under the new **Kit Order Lines** tab, with:
   - **Sale Order Line** — back-pointer to the parent SO line.
   - **Product** — the component product.
   - **Quantity** — `parent_qty * kit_line.product_qty`, converted
     through the parent's UoM.
   - **Unit Price** — taken from the component's contextual price
     (pricelist, partner, date, UoM).
   - **Tax** — copied from the parent SO line and recomputed.
   - **Subtotal** — recomputed via `tax_ids.compute_all`.

## Adjusting a kit on the order

- **Kit Order Lines** tab is editable: change quantities, prices,
  discounts, taxes or even the component product on a kit row.
- The parent SO line's **Unit Price** is recomputed automatically
  from `sum(kit_lines.price_subtotal) / parent.product_uom_qty`, so
  the customer-facing total stays in sync.
- Changing the parent SO line (product, quantity, taxes) re-explodes
  the kit lines on save: the existing kit rows are unlinked and a
  fresh set is generated from the kit definition.
- Removing the parent SO line cascades and removes its kit lines.

## Pricelist behaviour

Each kit line is priced through the order's pricelist using the
component's own UoM and quantity. Switching the order's pricelist
re-prices each kit line on the next save; promotions or
quantity-based rules on the component product apply directly.

## Limitations

- Re-explosion only runs while the order is in `draft` or `sent`. On
  confirmed / locked orders, kit lines can still be edited
  individually but the standard order line will not regenerate them.
- Kit lines are reference rows for pricing and reporting; they do
  not produce their own delivery or invoice unless other modules
  hook into `sale.order.line.kit` (e.g.
  `nexterp_product_kit_sale_timesheet` for tasks).
