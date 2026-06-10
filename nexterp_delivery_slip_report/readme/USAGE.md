# Daily use

The module changes the behaviour of the existing delivery slip print
actions — there is no new menu or wizard. Once installed and
configured, every delivery slip printed from a transfer uses the
inherited templates.

## Printing a delivery slip

1. Open a transfer from **Inventory -> Operations -> Transfers**.
2. Click **Print -> Delivery Slip**.
3. The generated PDF reflects the company options:
   - Product column shows the bare product name (no `[CODE]` prefix,
     no description) when *only name* is enabled.
   - Demand and done quantities are printed with the UoM-specific
     number of decimals when *uom precision* is enabled.
   - The PDF is rendered in the company partner's language for
     non-outgoing pickings when *lang company* is enabled.

## How it works

- `stock.report_delivery_document` is patched to replace
  `move.product_id` and conditionally hide `move.description_picking`.
- `stock.stock_report_delivery_has_serial_move_line` applies the same
  replacements on the per-serial-number view used for tracked
  products.
- `stock.stock_report_delivery_aggregated_move_lines` hides the
  aggregated description and consumes a `report_precision` value
  attached to each aggregated line.
- `StockMoveLine._get_aggregated_product_quantities` injects
  `report_precision` from the line UoM into the aggregated dict.
- `StockMoveLine._get_aggregated_properties` returns
  `product.name` (instead of the display name) when *only name* is on.
- `StockPicking._get_report_lang` returns the company partner language
  for non-outgoing pickings when *lang company* is on; the default
  behaviour is preserved for customer deliveries.
- `StockMoveLine._get_report_lang` picks the move partner language
  first, falling back to the line partner language and then to the
  user language.
