# Daily use

The flow is built around the `l10n.ro.stock.inventory` form. A single
record represents one physical inventory: pick a scope, generate the
lines from current stock, count, then validate.

## 1. Create an inventory

Go to **Inventory → Operations → Adjustments → Inventory Stock
Adjustments** and click **New**:

1. **Accounting Date** — defaults to today; the date the stock
   adjustments will be booked on.
2. **Locations** — pick one or more internal locations to count. Leave
   empty to count every internal location of the company.
3. **Products** — optionally restrict the inventory to a product list;
   leave empty to count every product on the selected quants.

Save the draft.

## 2. Generate the lines

Click **Generate Inventory Lines**. The wizard:

- Searches `stock.quant` for the configured scope.
- Skips quants that already have a line on this inventory (the action
  can be called multiple times while the inventory is in **Draft**).
- Creates one line per quant, snapshotting **On Hand Quantity**,
  **Counted Quantity**, **Difference**, **Standard Price** and
  **Value**.
- Sets `inventory_quantity = 0` on quants that had no value, so the
  counter starts from a blank slate.

## 3. Adjust the count

In the **Inventory Lines** tab:

- Edit **Counted Quantity** per line; **Difference** updates
  automatically through the related quant.
- Add manual lines for product / location / lot combinations not yet
  in stock — the create override on the line model finds the matching
  `stock.quant` (or creates one with `inventory_quantity = 0`).
- Click **Clear Inventory Lines** to wipe all lines and start over;
  the related quants' `inventory_quantity` is cleared as well.

## 4. Validate

Click **Validate Inventory**. The action:

1. Sets the accounting date on each quant.
2. Re-reads the final on-hand quantity, value and difference on each
   line.
3. Calls `stock.quant.action_apply_inventory()` on the quant, posting
   the stock-account journal entries.
4. Captures `inventory_value` (post-apply value) and
   `inventory_diff_value` on each line, then locks the document with
   **State = Done**.

## 5. Inverse capture from elsewhere

When users adjust quants directly from **Inventory → Operations →
Physical Inventory** or via imports, the override on
`stock.quant.action_apply_inventory` creates one
`l10n.ro.stock.inventory` per accounting date involved, generates its
lines from the affected quants and validates it immediately. Those
documents appear in the same list as user-created ones, marked
**Done**.

## 6. Reporting

Open **Inventory → Reporting → Inventory Stock Line Adjustments
History** for a flat list of every counted line. The view supports
list, pivot and graph layouts, with measures **On Hand Quantity**,
**Counted Quantity** and **Difference**, grouped by inventory or
state.
