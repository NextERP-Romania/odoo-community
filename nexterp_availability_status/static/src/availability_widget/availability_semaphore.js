/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

const EPS = 1e-6;

// Native Odoo selection values (stock.picking / mrp.production) -> semaphore.
const NATIVE_STATE_MAP = {
    available: "available",
    expected: "waiting",
    late: "waiting",
    unavailable: "unavailable",
};

function statusLabel(status) {
    switch (status) {
        case "available":
            return _t("Available");
        case "partial":
            return _t("Partially available");
        case "waiting":
            return _t("Waiting for transfer");
        default:
            return _t("Unavailable");
    }
}

/**
 * Read-only traffic-light for stock availability. It does NOT add any server
 * field: it derives its state purely from the standard Odoo fields already
 * present on the record, so the same widget works on stock.move, stock.picking,
 * mrp.production, sale.order.line and purchase.order.line.
 */
export class AvailabilitySemaphore extends Component {
    static template = "nexterp_availability_status.AvailabilitySemaphore";
    static props = {
        ...standardWidgetProps,
        title: { type: String, optional: true },
    };

    get data() {
        return this.props.record.data;
    }

    /** @returns {{status: string, ratio: number}} */
    get info() {
        const model = this.props.record.resModel;
        const d = this.data;
        const gte = (a, b) => a >= b - EPS;

        if (model === "stock.move") {
            const demand = d.product_uom_qty || 0;
            const reserved = d.quantity || 0;
            const forecast = d.forecast_availability || 0;
            const refQty = d.product_qty || 0;
            if (d.state === "cancel" || d.state === "draft") {
                return { status: "none", ratio: 0 };
            }
            if (demand <= EPS) {
                // Nothing to move/consume on this line (e.g. a component scoped
                // to 0 by a BOM attribute) -> no light instead of a misleading
                // "available" with no actual stock behind it.
                return { status: "none", ratio: 0 };
            }
            switch (d.state) {
                case "done":
                case "assigned":
                    return { status: "available", ratio: 1 };
                case "partially_available":
                    return {
                        status: "partial",
                        ratio: demand ? Math.min(reserved / demand, 1) : 0,
                    };
                case "waiting":
                    // Chained move waiting for its source transfer to be processed.
                    return { status: "waiting", ratio: 0 };
                default: // confirmed / draft
                    if (refQty && gte(forecast, refQty)) {
                        return { status: "waiting", ratio: 0 };
                    }
                    if (refQty && forecast > EPS) {
                        return { status: "partial", ratio: Math.min(forecast / refQty, 1) };
                    }
                    return { status: "unavailable", ratio: 0 };
            }
        }

        if (model === "sale.order.line") {
            const demand = d.product_uom_qty || 0;
            const free = d.free_qty_today || 0;
            const availToday = d.qty_available_today || 0;
            if (demand && gte(free, demand)) {
                return { status: "available", ratio: 1 };
            }
            if (availToday > EPS) {
                return {
                    status: "partial",
                    ratio: demand ? Math.min(availToday / demand, 1) : 0,
                };
            }
            if (d.forecast_expected_date) {
                return { status: "waiting", ratio: 0 };
            }
            return { status: "unavailable", ratio: 0 };
        }

        if (model === "purchase.order.line") {
            // forecasted_issue = the incoming qty still leaves a negative forecast.
            return d.forecasted_issue
                ? { status: "waiting", ratio: 0 }
                : { status: "available", ratio: 1 };
        }

        // stock.picking / mrp.production: reuse the native selection field.
        // A falsy value means cancelled/draft/not-applicable -> no light.
        const native = d.components_availability_state || d.products_availability_state;
        if (!native) {
            return { status: "none", ratio: 0 };
        }
        const status = NATIVE_STATE_MAP[native] || "unavailable";
        return { status, ratio: status === "available" ? 1 : 0 };
    }

    get label() {
        return statusLabel(this.info.status);
    }

    get tooltip() {
        // Prefer Odoo's own human-readable text when available.
        const d = this.data;
        return d.components_availability || d.products_availability || this.label;
    }

    get fillStyle() {
        const { status, ratio } = this.info;
        if (status !== "partial") {
            return "";
        }
        const pct = Math.round(Math.max(0, Math.min(1, ratio)) * 100);
        return `--ne-avail-fill: ${pct}%;`;
    }
}

export const availabilitySemaphore = {
    component: AvailabilitySemaphore,
    extractProps: ({ attrs }) => ({ title: attrs.title }),
};

registry.category("view_widgets").add("availability_semaphore", availabilitySemaphore);
