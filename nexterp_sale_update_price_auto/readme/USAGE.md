# Daily use

The module works in the background on every sale order / quotation
form. There is no new menu, no extra button and no wizard.

## Changing the pricelist on a quotation

1. Open a quotation from **Sales -> Orders -> Quotations** (or a
   confirmed order from **Sales -> Orders -> Orders**).
2. Make sure the order already has at least one line — the
   recomputation is skipped when the order is still empty.
3. Change the **Pricelist** field on the *Other Info* tab.
4. As soon as the field loses focus, the `onchange` runs:
   - line **Unit Prices** are refreshed against the new pricelist,
   - discounts attached to pricelist rules are reapplied,
   - if the order is already saved, a message appears in the chatter:
     *"Product prices have been recomputed according to pricelist
     `<pricelist name>`"*.
5. Save the order to persist the new prices.

## How it works

The override of `_onchange_pricelist_id_show_update_prices` checks the
following conditions before calling `_recompute_prices()`:

| Condition | Why |
|---|---|
| `self.order_line` truthy | Nothing to recompute on an empty order |
| `self.pricelist_id` set | No target pricelist, nothing to apply |
| `_origin.pricelist_id != self.pricelist_id` | The pricelist actually changed |
| `company.sale_auto_update_price` | Feature is enabled on the company |

The recomputation is called as `self.with_context(force_price_recomputation=True)._recompute_prices()`,
which forces the standard pricing engine to update lines even when
manual price overrides would normally block it.

## Reverting

To go back to the standard manual workflow, untick **Auto Update Sales
Prices** under **Sales -> Configuration -> Settings**. The next
pricelist change on a sale order will again show the **Update Prices**
banner instead of recomputing automatically.
