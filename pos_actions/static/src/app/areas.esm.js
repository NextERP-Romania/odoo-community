/** The desks a shop works at, and the line that lists them.
 *
 * Every screen added to the point of sale used to put a button of its own
 * next to Register and Orders. Five of them and the bar is full, on the one
 * line that also carries the order tabs and the search box -- and the next
 * one would make it worse rather than raise the question again.
 *
 * So the desks get a line of their own above the register, and a registry
 * to be listed in. A module no longer patches the bar: it declares where it
 * belongs, once, and the line is built from what is declared.
 */
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";

export const AREAS = "pos_actions_areas";

/** Register a desk.
 *
 * @param {String} id       what the area is called in code
 * @param {Object} area
 * @param {String} area.label    what the cashier reads
 * @param {String} area.icon     `data-icon` of the oi icon, for small screens
 * @param {Number} area.sequence where it sits on the line; the register is 0
 * @param {string[]} area.screens the screens that mean "we are here"
 * @param {Function} [area.open] what the button does; navigating to the
 *                               first screen is what it does by default
 * @param {Function} [area.isActive] when `screens` cannot say it: two desks
 *                               may share a screen and differ by the tab
 *                               they stand on. Declared areas are asked in
 *                               sequence, so the narrower one goes first.
 * @param {Function} [area.count] a number to show on the entry -- the work
 *                               waiting there -- or nothing for no badge.
 */
export function registerArea(id, area) {
    registry.category(AREAS).add(id, {id, ...area});
}

/** The declared desks, in the order they are meant to be read. */
export function areas() {
    return registry
        .category(AREAS)
        .getAll()
        .slice()
        .sort(
            (a, b) => (a.sequence || 0) - (b.sequence || 0) || a.id.localeCompare(b.id)
        );
}

// The register itself is a desk like the others, declared here so the line
// is built the same way whether or not a shop has any of the rest.
registerArea("register", {
    label: _t("Register"),
    icon: "edit",
    sequence: 0,
    screens: [],
    open: (pos) => pos.navigate("ProductScreen"),
});
