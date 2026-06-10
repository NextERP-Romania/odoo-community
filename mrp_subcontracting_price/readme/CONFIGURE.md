# Configuration

The module activates as soon as it is installed and a subcontracting
purchase flow exists. There is no settings page; configuration is
limited to making sure the upstream modules and master data are in
place.

## 1. Install dependencies

The manifest pulls two prerequisites that must be installable first:

- `l10n_ro_stock_account` — Romanian stock-account valuation (OCA).
- `mrp_subcontracting_purchase` — Odoo bridge between subcontracting
  BOMs and purchase orders.

Install both before this module.

## 2. Configure subcontracted products

Go to **Inventory → Products → Products** and open each finished good
that will be subcontracted:

1. Set the **Product Type** to a storable / consumable as usual.
2. On the **Inventory** tab, set **Costing Method** to **Standard
   Price**, **Average Cost (AVCO)** or **FIFO** as required.
3. Make sure **Valuation** is set to **Automated** (perpetual
   inventory) — the override only updates stock value on done moves;
   manual valuation would leave it untouched.

## 3. Configure the subcontracting BOM

Go to **Manufacturing → Products → Bills of Materials** and create a
BOM with:

1. **BOM Type** = **Subcontracting**.
2. **Subcontractors** = the supplier partners that will perform the
   service.
3. **Components** = the materials sent to the subcontractor.

## 4. Configure the purchase product (the service)

The amount the subcontractor charges should be the unit price of the
purchase order line for the finished good. Standard Odoo subcontracting
expects you to buy the finished product itself; that line's price
becomes the receipt value.

If the service is invoiced as a separate purchase product, it must
sit on the same PO so that `move_orig_ids` chains the receipt to the
purchase price.

## 5. User access

No new security groups are added. Users handling subcontracting need
their existing **Manufacturing**, **Inventory** and **Purchase**
groups. Valuation updates run with the user posting the receipt.

## 6. Verification

After installation, post a subcontracted receipt and open the
**Valuation Layer** of the finished good. The amount should match the
purchase line value at the received quantity, not a recomputation from
the component standard prices.
