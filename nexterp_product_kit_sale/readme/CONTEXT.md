# Key features

- New model `sale.order.line.kit` (inherits `sale.order.line`) that
  stores the exploded component lines, linked back to the parent SO
  line via `sale_line_id`.
- New one2many `kit_line_ids` on both `sale.order` (all kit lines of
  the order) and `sale.order.line` (kit lines for that SO line).
- Automatic explosion on `create` and on `write` for orders in
  `draft` or `sent` state: `generate_sale_order_line_kit` re-creates
  the kit lines from `product.product.kit` whenever the order lines
  change.
- Per-component pricing through the order's pricelist, partner,
  currency, UoM and date — taxes are recomputed via
  `tax_ids.compute_all` so `price_tax`, `price_subtotal` and
  `price_total` are kept consistent on each kit line.
- Parent SO line `price_unit` is recomputed from the sum of the kit
  lines' subtotals through `get_sale_kit_price`, so the customer
  sees the kit as a single priced line.
- Recursion guard via the `change_from_soline` context key avoids
  loops between parent and kit line writes.
- Orphan-line cleanup: stale `sale.order.line.kit` rows whose
  `sale_line_id` was reset by a one2many replace are unlinked
  automatically on write.
- Dedicated **Kit Order Lines** tab on the sale order form, grouped
  by SO line, with editable quantities, prices, taxes and UoM.
- Cascade `unlink` from `sale.order.line` cleans the related kit
  lines; `_check_line_unlink` is overridden so kit rows are always
  deletable.
- `product_document_ids` and `invoice_lines` are mirrored on kit
  lines for document attachments and invoicing hooks.
