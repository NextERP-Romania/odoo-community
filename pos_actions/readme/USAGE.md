# Daily use

Nothing to do. The line appears above the register bar as soon as a module
that declares a desk is installed, with **Register** on the left and the
desks after it in the order their authors gave them.

Tapping an entry opens that desk; the one you are standing at is lit. On a
small screen the labels give way to icons, as the register bar's own
buttons do.

# For a module author

Declare the desk once, in an asset loaded into `point_of_sale._assets_pos`:

```js
import {registerArea} from "@pos_actions/app/areas";
import {_t} from "@web/core/l10n/translation";

registerArea("labels", {
    label: _t("Labels"),
    icon: "sell",          // oi data-icon, shown on small screens
    sequence: 35,
    screens: ["LabelScreen"],
});
```

Then nothing else: no patch of the navigation bar, no `mainButton`, no
ordering fought out in CSS. The entries are asked in `sequence` order which
of them is the active one, so a desk that narrows another — same screen,
different tab — is declared before it and answers first.
