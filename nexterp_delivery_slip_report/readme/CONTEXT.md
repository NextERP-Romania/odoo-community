# Key features

- Inherits the three standard delivery PDF templates at priority 100:
  `stock.report_delivery_document`,
  `stock.stock_report_delivery_has_serial_move_line` and
  `stock.stock_report_delivery_aggregated_move_lines`.
- **Delivery slip report only name** — replaces the product display
  name (which prepends the internal reference) with the bare
  `product_id.name`, and hides the `move.description_picking` /
  aggregated description so the product column is cleaner.
- **Delivery slip report uom precision** — formats the demand and done
  quantity using the `report_precision` defined per UoM (field
  inherited from `nexterp_account_invoice_report`), so quantities are
  printed with the correct number of decimals for kg / l / m / etc.
- **Picking report lang company** — for non-outgoing pickings
  (receipts, internal transfers, returns…), forces the report language
  to the company partner's language. Customer deliveries still print
  in the customer's language.
- All three switches are independent and can be combined.
- Depends on `nexterp_account_invoice_report` to reuse the
  `uom.uom.report_precision` field.
- The aggregated-lines variant also propagates `report_precision`
  through `_get_aggregated_product_quantities`, and the override of
  `_get_aggregated_properties` strips the `[CODE]` prefix from the
  printed product name when *only name* is on.
