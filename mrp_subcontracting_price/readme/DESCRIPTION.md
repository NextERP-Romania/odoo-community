Override stock valuation for subcontracted finished goods so the price
of the incoming receipt is taken from the purchase line — the price
actually paid to the subcontractor — instead of being recomputed from
the components shipped out. The standard Odoo behaviour assumes the
company knows the component cost at receipt time, which is rarely the
case when materials are owned by the subcontractor or are valued
upstream.

The module re-uses the origin move's value when the incoming
subcontracted move and all its origins are `done`, so the receipt
inherits the subcontracting service price from the related vendor
bill / purchase order line. The trigger is wired into
`stock.move._action_done` so the post-receipt valuation runs
automatically, without manual relayering or extra accounting steps.

Intended for Romanian manufacturers and traders running subcontracted
production where the conversion service is invoiced as a single line
on the PO, and the resulting finished good must enter stock at that
service price plus any sent-out component cost already booked on the
outgoing leg.
