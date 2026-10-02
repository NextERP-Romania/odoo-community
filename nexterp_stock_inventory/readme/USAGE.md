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

## 5. Print the inventory report

The *proces verbal de inventariere* is printed from the same form, with
the **Print Inventory Report** button in the header or from the
**Print** menu. Fill in the documentary data first:

- **Inventory Report** group — **Decision Number**, the decision
  appointing the commission. The group also shows the read-only
  **Surplus**, **Shortage** and **Difference** totals. The document is
  dated by the **Accounting Date** of the inventory itself.
- **Inventory Commission** tab — one line per member: pick a **User**
  to fill the name automatically or type it, then the **Job Position**
  and the **Role** (Chairman, Member or Stock Keeper). The order of the
  lines is the order they are printed in, and can be changed by drag
  and drop.
- **Conclusions** tab — free text with the conclusions and proposals of
  the commission, printed at the end of the report.

The PDF lists only the lines whose counted quantity differs from the
quantity on hand, valued the way the location carries them — at cost
here, at shelf price where a module says otherwise. Each difference is valued in `inventory_diff_value`
as soon as the quantity is counted, the same way the adjustment will
book it: a surplus at the current cost, a shortage at the FIFO layers
it consumes or at the standard / average price, with lot valuation
honoured when the product uses it. The figure therefore does not change
on validation, so the draft report and the final one show the same
amounts.

## 6. Inverse capture from elsewhere

When users adjust quants directly from **Inventory → Operations →
Physical Inventory** or via imports, the override on
`stock.quant.action_apply_inventory` creates one
`l10n.ro.stock.inventory` per accounting date involved, generates its
lines from the affected quants and validates it immediately. Those
documents appear in the same list as user-created ones, marked
**Done**.

## 7. Reporting

Open **Inventory → Reporting → Inventory Stock Line Adjustments
History** for a flat list of every counted line. The view supports
list, pivot and graph layouts, with measures **On Hand Quantity**,
**Counted Quantity** and **Difference**, grouped by inventory or
state.
