/** The cash register, declared as one of the shop's desks. */
import {registerArea} from "@pos_actions/app/areas";
import {_t} from "@web/core/l10n/translation";

registerArea("cash_register", {
    label: _t("Cash Register"),
    icon: "account_balance_wallet",
    sequence: 40,
    screens: ["CashRegisterScreen"],
});
