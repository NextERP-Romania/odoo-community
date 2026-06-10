Define composite products (kits) made up of one or more component
products. A kit is a regular `product.product` that holds a list of
component lines, each with its own quantity and unit of measure;
components are individual storable or service products flagged as
**Is a Kit Component** so they are excluded from direct sale.

The module computes the kit's cost and list price from the sum of its
components: `_price_compute` aggregates `standard_price` and
`lst_price` of every component multiplied by its line quantity, and
the pricelist engine (`_compute_price_rule`) returns the kit price
based on each component's pricelist entry rather than a flat list
price. This keeps the kit price consistent when component prices or
pricelists change.

Targets sales catalogs built from reusable components — service
bundles, hardware-plus-installation packs, or any product sold as a
single SKU but priced and tracked as a sum of parts.
