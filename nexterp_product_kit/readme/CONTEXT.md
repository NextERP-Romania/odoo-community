# Key features

- New model `product.product.kit` storing the component lines of every
  kit product (component product, quantity, unit price, unit of
  measure).
- Boolean field **Is a Kit Component** on `product.template` and
  `product.product`; ticking it automatically clears **Can be Sold**
  via an onchange.
- Kit lines exposed on both the product template form and the
  per-variant easy-edit form via a dedicated **Kit Products**
  notebook tab.
- Kit list price (`lst_price`) recomputed from component
  `product_qty * product_price`, with pricelist and target UoM taken
  into account through `_compute_product_lst_price`.
- Cost price (`standard_price`) and any other price type aggregated
  from components in `_price_compute`, so reports and valuations stay
  consistent.
- Pricelist override (`product.pricelist._compute_price_rule`):
  whenever a pricelist is applied to a kit product, the engine sums
  the components' contextual prices for the requested quantity, UoM
  and date.
- Dedicated **Product Kits** menu under
  **Sales → Products** with list, form, pivot and grouping search
  views (restricted to the Sales Manager group).
