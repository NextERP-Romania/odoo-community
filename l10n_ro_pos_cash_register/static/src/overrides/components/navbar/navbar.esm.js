/** One tap from the register to the cash register, and one tap back. */
import {Navbar} from "@point_of_sale/app/components/navbar/navbar";
import {patch} from "@web/core/utils/patch";

patch(Navbar.prototype, {
    openCashRegister() {
        this.pos.navigate("CashRegisterScreen");
    },

    /** Core lights up Orders for every screen that is not a selling one.
     *  This one is neither: its own button says where we are. */
    get mainButton() {
        if (this.pos.router.currentScreen() === "CashRegisterScreen") {
            return "cash-register";
        }
        return super.mainButton;
    },
});
