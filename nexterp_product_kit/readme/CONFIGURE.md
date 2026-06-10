# Configuration

## 1. Mark the component products

1. Go to **Sales → Products → Products** (or **Inventory → Products
   → Products**).
2. Open each product that should act as a kit component.
3. Under the **General Information** tab, in the *Options* area, tick
   **Is a Kit Component**. **Can be Sold** is cleared automatically,
   so components stay out of the regular sales catalog.
4. Save.

## 2. Define the kit product

1. Open (or create) the product that represents the kit itself.
2. Leave **Is a Kit Component** unticked and keep **Can be Sold**
   active.
3. Open the **Kit Products** tab.
4. Add one line per component:
   - **Component Product** — the component flagged at step 1.
   - **Quantity** — how many units of that component the kit
     contains.
   - **Unit of Measure** — pulled from the component product.
   - **Price** — auto-computed as `quantity * component list price`.
5. Save. The kit's **Sales Price** and **Cost** are now computed
   from the sum of its components.

## 3. Per-variant kit definition (optional)

For products with variants, open a variant from the **Variants**
smart button and use the **Kit Products** tab on the variant form to
define a variant-specific component list.

## 4. Browse all kits

The **Sales → Products → Product Kits** menu (Sales Manager group)
provides a global list / pivot view of every kit line in the
database.
