Explode product kits into per-component lines on Sale Orders. When
a sale order line carries a kit product, the module mirrors the kit
definition (`product.product.kit`) into a dedicated `Kit Order Lines`
tab on the order, one row per component, with quantities and prices
priced through the order's pricelist, partner, currency and fiscal
position.

Kit lines live in a new model `sale.order.line.kit` that inherits
`sale.order.line` for behaviour reuse but is detached from the main
`order_line` field, so the customer-facing order shows the kit as a
single SKU while accounting, invoicing and reporting still see the
detailed components through the dedicated table.

Edits flow both ways: changing a kit line's quantity, price, tax or
product reprices the parent SO line via `get_sale_kit_price`, and
deleting the parent SO line cascades through `unlink`. Orphan kit
rows left over from one2many resets are swept on every write, so the
explosion stays in sync with the order line.
