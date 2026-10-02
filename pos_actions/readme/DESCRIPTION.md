Every screen added to the point of sale used to put a button of its own
next to **Register** and **Orders**. Five of them and the bar is full — on
the one line that also carries the order tabs and the search box — and the
next one would make it worse rather than raise the question again.

So the desks get a line of their own, above the register bar: *Register*,
*Purchases*, *Warehouse*, *Expenses*, *Labels*, *Cash Register*, and
whatever comes next. The bar the point of sale ships keeps its line
underneath, unchanged.

The point is not the line. It is that a module no longer patches the
navigation bar to get onto it: it declares where it belongs, once, in a
registry, and the line is built from what is declared. The eighth desk is
an entry, not another argument about crowding.

```js
import {registerArea} from "@pos_actions/app/areas";

registerArea("warehouse", {
    label: _t("Warehouse"),
    icon: "inventory_2",
    sequence: 20,
    screens: ["WarehouseScreen"],
});
```

A desk that shares a screen with another and differs by the tab it stands
on says so with `isActive`; one that has work waiting shows it with
`count`; one that has to put its screen in order before opening does it in
`open`.
