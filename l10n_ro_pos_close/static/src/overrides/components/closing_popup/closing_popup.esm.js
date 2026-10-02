/** The cause of a closing difference, written down where it is noticed.
 *
 *  The cashier is the only one who knows why the card is short by what the
 *  drawer holds too much, and they know it at the register, not the next
 *  morning in the back office. The popup that already shows the difference
 *  is where it is asked for.
 */
import {ClosePosPopup} from "@point_of_sale/app/components/popups/closing_popup/closing_popup";
import {patch} from "@web/core/utils/patch";

patch(ClosePosPopup.prototype, {
    getInitialState() {
        const state = super.getInitialState();
        // Every method the popup can count, not only the ones counted now:
        // the template reads this while the cashier types, and an entry
        // created during a render would make the dialog render itself again.
        state.l10nRoExplanations = {};
        for (const method of this.l10nRoCountableMethods) {
            state.l10nRoExplanations[method.id] = {reason: "", note: ""};
        }
        return state;
    },

    /** The methods whose count the popup compares, cash first.
     *
     *  Cash only when the register counts it: without cash control there is
     *  no counted amount to compare, and core's getDifference would read one
     *  that is not there.
     */
    get l10nRoCountableMethods() {
        const methods = [];
        if (this.pos.config.cash_control && this.props.default_cash_details?.id) {
            methods.push(this.props.default_cash_details);
        }
        methods.push(
            ...this.props.non_cash_payment_methods.filter((pm) => pm.type === "bank")
        );
        return methods;
    },

    /** Of those, the ones that did not match -- what the report is about.
     *
     *  Same test as the overview above makes: a bank method the register
     *  took no payment on is not counted, so it cannot be short either.
     */
    get l10nRoMethodsWithDifference() {
        return this.l10nRoCountableMethods.filter((method) => {
            if (method.number === 0 || !this.state.payments[method.id]) {
                return false;
            }
            const difference = this.getDifference(method.id);
            return !isNaN(difference) && !this.pos.currency.isZero(difference);
        });
    },

    async closeSession() {
        // Before core closes, because afterwards the popup is gone and the
        // session is read only.
        await this.l10nRoSaveExplanations();
        return super.closeSession();
    },

    async l10nRoSaveExplanations() {
        const explanations = {};
        for (const method of this.l10nRoMethodsWithDifference) {
            const typed = this.state.l10nRoExplanations[method.id];
            if (typed && (typed.reason || typed.note)) {
                explanations[method.id] = {reason: typed.reason, note: typed.note};
            }
        }
        await this.pos.data.call("pos.session", "l10n_ro_set_closing_explanations", [
            this.pos.session.id,
            explanations,
            // Core collects the closing note in this popup and never sends
            // it; it is the note of the report of differences.
            this.state.notes,
        ]);
    },
});
