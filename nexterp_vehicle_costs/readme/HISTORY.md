# Changelog

## 19.0.1.1.0 (2026-11-05)

- A vehicle cost booked from a done stock move follows the move: its amount,
  vehicle, product and quantities cannot be edited and it cannot be deleted;
  notes stay editable. Costs typed by hand are not affected.
- The vehicle (or the refuelling flag) of a done move that already has a cost
  cannot be changed any more.
- Returning goods from the vehicle's consumption location books a negative
  cost on the same vehicle, reversing the original one.
- Contract-type service categories are recognised (the comparison used
  `"Contract"` instead of `"contract"`).
- Uninstalling the module turns the fuel and parts service types into plain
  services instead of deleting them together with their costs.
- Cancelling a vendor bill removes the vehicle service costs made from its
  lines when it was posted (posting it again makes them anew).
- Removed code that could never run: a `stock.move.action_cancel` override
  (there is no such method), a bill-line cost cancellation on fields that do
  not exist, and the unused vehicle cost counters on journal entries.
- Romanian translation added.

## 19.0.1.0.1 (2026-08-21)

- _Changelog tracking starts at this release._
