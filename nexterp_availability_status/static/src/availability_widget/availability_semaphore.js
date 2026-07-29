/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

// Status code -> visual colour class. The rich, translated text comes from the
// server field `availability_status_label`; here we only pick the light colour.
const COLOR = {
    available: "available",       // green
    partial: "partial",          // half green
    // amber: in progress / expected
    reception: "waiting",
    transfer: "waiting",
    to_transfer: "waiting",
    mo_planned: "waiting",
    po_draft: "waiting",
    mo_draft: "waiting",
    mo_unplanned: "waiting",
    // red: nothing on the way / late
    to_order: "unavailable",
    to_manufacture: "unavailable",
    reception_late: "unavailable",
    transfer_late: "unavailable",
    mo_late: "unavailable",
    unavailable: "unavailable",
};

/**
 * Read-only traffic-light for stock availability. It renders the status
 * computed on the server (availability_status_code / _label / availability_ratio),
 * so the exact same widget works on stock.move, stock.picking, mrp.production,
 * sale.order.line and purchase.order.line.
 */
export class AvailabilitySemaphore extends Component {
    static template = "nexterp_availability_status.AvailabilitySemaphore";
    static props = {
        ...standardWidgetProps,
        title: { type: String, optional: true },
    };

    get code() {
        return this.props.record.data.availability_status_code || "none";
    }

    get color() {
        return COLOR[this.code] || "none";
    }

    get label() {
        return this.props.record.data.availability_status_label || "";
    }

    get tooltip() {
        return this.label;
    }

    get ratio() {
        const r = this.props.record.data.availability_ratio || 0;
        return Math.max(0, Math.min(1, r));
    }

    get fillStyle() {
        if (this.color !== "partial") {
            return "";
        }
        return `--ne-avail-fill: ${Math.round(this.ratio * 100)}%;`;
    }
}

export const availabilitySemaphore = {
    component: AvailabilitySemaphore,
    fieldDependencies: [
        { name: "availability_status_code", type: "selection" },
        { name: "availability_status_label", type: "char" },
        { name: "availability_ratio", type: "float" },
    ],
    extractProps: ({ attrs }) => ({ title: attrs.title }),
};

registry.category("view_widgets").add("availability_semaphore", availabilitySemaphore);
