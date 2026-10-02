# Daily use

Count and validate as usual, from **Inventory → Operations →
Adjustments → Inventory Stock Adjustments**. Nothing changes in the
flow; the shop lines simply carry three more figures.

## On the inventory

The **Inventory Lines** tab gains **Markup (378)**, **Deferred VAT
(4428)** and **Retail Value (371)**, each summed at the bottom, plus an
optional **Shelf Price** column. They fill in as soon as the counted
quantity is entered and are refreshed just before the adjustment is
booked, so what the document shows is what the entry posts.

The **Inventory Report** group of the header shows the same three
totals for the whole document, next to the cost totals.

## On the printed report

The differences of a shop are stated at the PVA throughout the
document: the per-location summary, the **Unit Price**, **Surplus** and
**Shortage** columns and their totals all carry the shelf price, since
that is what account 371 holds and what the shop answers for. A
location that is not a shop keeps printing at cost, so a document
covering both states each *gestiune* at the value it carries.

**Print Inventory Report** then adds a *Differences at shelf price*
section breaking those amounts down, for the lines held in a retail
location:

| Column | Meaning |
| --- | --- |
| Difference | counted quantity less the quantity on hand |
| Shelf Price | the PVA the shop charges today, VAT included |
| Cost | the cost difference, as on the previous table |
| Markup (378) | the commercial markup released or loaded |
| Deferred VAT (4428) | the VAT included in the shelf price |
| Retail Value (371) | the three added up: what 371 moves by |

The section is left out entirely when the inventory covers no retail
location, so a company counting a plain warehouse prints the same
document as without this module.

## How the figures are reached

- A **surplus** is valued from the retail pricelist of the shop: the
  markup is the shelf price without VAT less the unit cost of the
  goods coming in, and the deferred VAT is the VAT inside the shelf
  price.
- A **shortage** is valued from `l10n.ro.retail.markup.line`, never
  from today's pricelist: the release has to match what was loaded, so
  the balance carried is prorated over the quantity carrying it. When
  the ledger carries no more than what is missing, both accounts close
  to zero.

That is the same rule the stock move itself applies, which is what lets
the report be reconciled line by line against 378 and 4428.
