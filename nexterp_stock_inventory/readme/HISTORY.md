# Changelog

## 20.0.1.1.0 (2026-10-02)

- Add the printable inventory report (*proces verbal de inventariere*):
  commission members, appointing decision, conclusions and a
  `Print Inventory Report` button on the inventory form.
- Value the counted difference in `inventory_diff_value` as soon as the
  quantity is entered, the way the adjustment will book it, through the
  new `_update_diff_values()` hook on the inventory line.
- Draw the printed figures through `_report_diff_value()` and
  `_report_totals()`, so a module holding the goods at another value can
  restate the document.

## 19.0.1.0.0 (2026-05-25)

- _Changelog tracking starts at this release._
