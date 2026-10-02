/** The desk line above the register bar. */
import {areas} from "@pos_actions/app/areas";
import {Navbar} from "@point_of_sale/app/components/navbar/navbar";
import {patch} from "@web/core/utils/patch";

patch(Navbar.prototype, {
    get posActionsAreas() {
        return areas();
    },

    /** Where we are, by the screen we are on.
     *
     *  A desk names the screens that mean it; anything else is the
     *  register, which is why the register declares none. Read off the
     *  router rather than remembered, so arriving at a screen by any other
     *  road still lights the right entry.
     */
    get posActionsActiveArea() {
        const screen = this.pos.router.currentScreen();
        const found = this.posActionsAreas.find((area) =>
            area.isActive
                ? area.isActive(this.pos)
                : (area.screens || []).includes(screen)
        );
        return found || this.posActionsAreas.find((area) => area.id === "register");
    },

    /** The work waiting at a desk, where it says so. */
    posActionsCount(area) {
        const count = area.count ? area.count(this.pos) : 0;
        return count > 0 ? count : false;
    },

    openPosActionsArea(area) {
        if (area.open) {
            return area.open(this.pos);
        }
        const screen = (area.screens || [])[0];
        if (screen) {
            this.pos.navigate(screen);
        }
    },
});
