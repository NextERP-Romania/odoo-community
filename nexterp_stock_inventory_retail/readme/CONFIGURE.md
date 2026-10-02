# Configuration

The module has nothing of its own to configure; it reads the retail
setup of `l10n_ro_stock_account_retail`.

1. Tick **Retail Warehouse** on the warehouse of the shop and give it a
   **Retail Pricelist** (*Inventory → Configuration → Warehouses*). All
   internal locations under it become retail locations, and only those
   lines get the markup columns.
2. Make sure every product counted in the shop has a rule on that
   retail pricelist. A product without one is left at zero instead of
   being given an invented markup — the same products the stock moves
   would refuse.
3. Check the **378** and **4428** accounts resolve, on the location,
   the product, the category or the company, as the retail module
   documents.
