# Changelog

## 19.0.1.1.0 (2026-11-05)

- A validated inventory is frozen: it cannot be validated again, regenerated,
  cleared, edited or deleted, and neither can its lines. A draft one deletes
  with its lines.
- Validating applies the counted quantities directly, also when goods moved
  after the count, and marks the document done only once the stock was
  adjusted. Before, Odoo's conflict wizard was returned and ignored: nothing
  was applied, yet the inventory was set to done.
- An adjustment made on the quants that ends in Odoo's conflict wizard no
  longer leaves a done inventory behind; the document is made when the
  conflict is settled. The `date` argument is passed on to Odoo.
- Lines keep their unit of measure after the quant they counted is cleaned
  up; their location, product and lot cannot be changed once the quant is
  set; goods tracked by lot cannot be counted in without one.
- The company of the inventory and the inventory of a line are now required
  (lines are deleted with their draft inventory); orphan lines are dropped on
  upgrade.

## 19.0.1.0.0 (2026-05-25)

- _Changelog tracking starts at this release._
