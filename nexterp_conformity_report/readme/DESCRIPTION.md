`nexterp_conformity_report` adds a *Certificate of Conformity*
(declarație de conformitate) PDF report on `stock.picking`. The report
is attached as a print binding on the picking form, so it is available
from the standard **Print** menu for any delivery in the *Done* state.

The certificate is structured around the data already present on the
delivery: customer information, picking number, dispatch date, the
related sale order reference (and the customer order reference, when
filled). It then lists every move line of the picking — product name,
custom customer product code, lot number, unit of measure, quantity
shipped and minimum shelf life (lot expiration date) — followed by a
boilerplate declaration in which the issuing company guarantees that
the delivered products meet food-safety regulations.

A signature block for the agent, delegate (with means of transport),
and a "shipment made in our presence" line are rendered at the bottom
so the document is ready to be signed at hand-over. The module depends
on `sale_stock` and on `l10n_ro_stock_picking_comment_template`.
