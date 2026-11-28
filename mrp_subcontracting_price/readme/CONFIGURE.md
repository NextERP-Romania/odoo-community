1. Install `l10n_ro_stock_account` and the Odoo **Subcontracting** purchase
   bridge (`mrp_subcontracting_purchase`); this module needs both.
2. For each subcontracted product, go to **Inventory > Products > Products**
   and make sure its product category uses automated (perpetual) inventory
   valuation.
3. Go to **Manufacturing > Products > Bills of Materials** and create a bill of
   materials of type **Subcontracting**, with the subcontractors and the
   components they receive.

There are no settings of its own and no new access groups.
