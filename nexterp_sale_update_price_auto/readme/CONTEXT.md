# Key features

- Overrides `sale.order._onchange_pricelist_id_show_update_prices` so
  the pricelist change behaves as an *apply* action rather than just
  showing the *Update Prices* banner.
- Triggers `_recompute_prices()` with the context flag
  `force_price_recomputation=True` so prices are refreshed even for
  lines that would normally be skipped by the standard guard.
- Recomputation only runs when **all** of the following are true:
  - the sale order already has at least one line (`self.order_line`),
  - a pricelist is set on the order (`self.pricelist_id`),
  - the pricelist has actually changed
    (`self._origin.pricelist_id != self.pricelist_id`),
  - the company has *Auto Update Sales Prices* enabled.
- When the order is already saved, a chatter message is posted on the
  original record stating which pricelist drove the recomputation,
  giving an audit trail of automatic price changes.
- Driven by a single boolean field, `sale_auto_update_price`, defined
  on `res.company` and exposed via `res.config.settings`.
- The setting is added to the Sales configuration form right after the
  standard `pricelist_configuration` block, so it stays grouped with
  the other pricelist-related options.
- Depends only on `sale_management`; no UI on the sale order itself.
