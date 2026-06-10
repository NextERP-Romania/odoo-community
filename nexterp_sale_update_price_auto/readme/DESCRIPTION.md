`nexterp_sale_update_price_auto` removes one manual step from the
quotation flow: when the pricelist on a sale order changes, prices on
the existing order lines are recomputed automatically instead of
waiting for the salesperson to click the **Update Prices** banner.

The module hooks into the standard
`_onchange_pricelist_id_show_update_prices` on `sale.order`. When the
sale order already has lines, the new pricelist differs from the
previous one, and the company has *Auto Update Sales Prices* enabled,
the override calls `_recompute_prices()` with the
`force_price_recomputation=True` context. If the order is already
saved (`_origin.id` is set), an audit message is posted in the
chatter recording which pricelist was applied.

The feature is gated by a company-level setting on `res.company`, so
it can be activated only on the companies that actually want this
behaviour, while other companies in the database keep the manual
"Update Prices" workflow.
