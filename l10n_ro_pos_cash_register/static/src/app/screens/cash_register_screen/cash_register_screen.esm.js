/** The cash register of every session this till has had.
 *
 * A shop keeping its takings in a drawer owes a *registru de casă* for each
 * day the drawer was open, and that is what a session is: it opens on a
 * counted balance, everything is written against it, and it closes on
 * another count. The screen lists them and hands over the document.
 *
 * The figures next to each session are there so the list answers the
 * question without opening the paper: what was counted at the open, what
 * moved, what the drawer should hold, what was actually counted -- and the
 * gap between those last two, which is the only one that can surprise
 * anybody.
 */
import {Component, onWillStart} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {usePos} from "@point_of_sale/app/hooks/pos_hook";
import {useService} from "@web/core/utils/hooks";

export class CashRegisterScreen extends Component {
    static template = "l10n_ro_pos_cash_register.CashRegisterScreen";
    static storeOnOrder = false;

    setup() {
        this.pos = usePos();
        this.ui = useService("ui");
        this.notification = useService("notification");
        // The point of sale's own way of handing a back-office document to
        // whoever is standing at the till.
        this.report = useService("report");
        this.state = this.pos.cashRegisterState;
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        try {
            this.state.sessions = await this.pos.data.call(
                "pos.config",
                "pos_cash_register_sessions",
                [this.pos.config.id]
            );
        } catch {
            this.notification.add(_t("The sessions could not be read."), {
                type: "danger",
            });
            this.state.sessions = [];
        } finally {
            this.state.loading = false;
        }
    }

    /** `false` where the localisation is not installed, and then nothing is
     *  offered: a button that cannot print is worse than no button. */
    get report_name() {
        return this.pos.config._pos_cash_register_report || false;
    }

    get sessions() {
        const search = (this.state.search || "").trim().toLowerCase();
        if (!search) {
            return this.state.sessions;
        }
        return this.state.sessions.filter((session) =>
            `${session.name} ${session.user}`.toLowerCase().includes(search)
        );
    }

    formatCurrency(amount) {
        return this.env.utils.formatCurrency(amount || 0);
    }

    formatMoment(value) {
        if (!value) {
            return "";
        }
        return luxon.DateTime.fromSQL(value).toFormat("dd/MM/yyyy HH:mm");
    }

    canPrint(session) {
        return Boolean(this.report_name && session.statement_id);
    }

    async print(session) {
        if (!this.canPrint(session)) {
            this.notification.add(
                _t("This session kept no cash, so it has no register."),
                {type: "warning"}
            );
            return;
        }
        try {
            await this.report.doAction(this.report_name, [session.statement_id]);
        } catch {
            this.notification.add(_t("The register could not be printed."), {
                type: "danger",
            });
        }
    }

    close() {
        this.pos.navigate("ProductScreen");
    }
}

registry.category("pos_pages").add("CashRegisterScreen", {
    name: "CashRegisterScreen",
    component: CashRegisterScreen,
    route: `/pos/ui/${odoo.pos_config_id}/cash-register`,
    params: {},
});
