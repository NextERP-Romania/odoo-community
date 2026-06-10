# Key features

- Adds a new QWeb-PDF action **Conformity Report** on `stock.picking`,
  available as a print binding (`binding_type=report`) from the
  picking form *Print* menu.
- Header block prints the customer address, VAT number (using the
  fiscal country's VAT label) and the trade-register number (`nrc`).
- Title block shows the picking number, the dispatch date (uses
  `l10n_ro_accounting_date` when present, otherwise `date_done` /
  `scheduled_date`) and the related sale order or customer order
  reference (`client_order_ref`).
- Move-line table renders one row per `move.line` with: row number,
  product name, customer-specific product code (read from
  `product.customer_ids` when the field exists), lot number, UoM,
  quantity done and lot **expiration date** as minimum shelf life.
- Conformity declaration paragraph cites the company name, city and
  street and the picking name + date.
- Footer signature block with agent details, sale order reference and
  a delegate panel (name, ID, means of transport `l10n_ro_mean_transp`,
  date / hour and dual signature lines).
- Report is rendered in the company partner language; the file name
  follows the pattern `Conformity_Report - <picking name>.pdf`.
- The certificate body is only rendered for pickings in state `done`.
