/** What the screen remembers between two visits.
 *
 * Kept on the store, not on the component: the screen is thrown away every
 * time the cashier steps back to the register, and the list it had just
 * read would be read again for nothing.
 */
import {PosStore} from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";
import {proxy} from "@odoo/owl";

patch(PosStore.prototype, {
    async setup(...args) {
        await super.setup(...args);
        this.cashRegisterState = proxy({
            sessions: [],
            loading: false,
            search: "",
        });
    },
});
