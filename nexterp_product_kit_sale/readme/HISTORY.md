# Changelog

## 19.0.1.1.0 (2026-11-05)

- The kit detail lines are frozen once the order is confirmed or the kit line
  invoiced: they can no longer be edited, added or deleted (in the form and on
  the server), so they cannot rewrite the price of a kit already billed.
  Before, deleting them was always allowed.
- On a confirmed order the kit line cannot change product, unit or quantity
  any more, since its detail lines would no longer match; the description and
  the other fields stay editable.
- Deleting a kit detail line no longer risks endless recursion when its id
  matched the id of a sales order line.

## 19.0.1.0.0 (2026-05-25)

- _Changelog tracking starts at this release._
