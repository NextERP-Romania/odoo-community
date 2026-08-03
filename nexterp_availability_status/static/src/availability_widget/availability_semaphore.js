/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

// Status code -> visual colour class. The rich, translated text comes from the
// server field `availability_status_label`; here we only pick the light colour.
const COLOR = {
    available: "available",       // green
    available_sub: "available",   // green (label notes it is in a sub-location)
    partial: "partial",          // half green
    // "split": half amber / half green dot = it will be fine (green) but with a
    // caveat - stock is in another location, or production is running late.
    to_transfer: "split",
    mo_late: "split",
    // amber: replenishment needed / in progress
    reception: "waiting",
    production: "waiting",
    // red: blocking - nothing on the way / document not validated
    to_order: "unavailable",
    to_manufacture: "unavailable",
    po_draft: "unavailable",
    mo_draft: "unavailable",
    unavailable: "unavailable",
};

/**
 * Read-only traffic-light for stock availability. Bound to
 * `availability_status_code`, it renders the status computed on the server
 * (code + `availability_status_label` + `availability_ratio`). The same widget
 * works on stock.move, stock.picking, mrp.production and sale.order.line.
 *
 * `options="{'compact': true}"` shows only the dot (text on hover) for dense
 * line grids; without it the label is shown inline.
 */
export class AvailabilitySemaphore extends Component {
    static template = "nexterp_availability_status.AvailabilitySemaphore";
    static props = {
        ...standardFieldProps,
        compact: { type: Boolean, optional: true },
    };

    get data() {
        return this.props.record.data;
    }

    get code() {
        return this.data.availability_status_code || "none";
    }

    get color() {
        return COLOR[this.code] || "none";
    }

    get label() {
        return this.data.availability_status_label || "";
    }

    get tooltip() {
        return this.label;
    }

    get ratio() {
        const r = this.data.availability_ratio || 0;
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
    supportedTypes: ["selection"],
    fieldDependencies: [
        { name: "availability_status_label", type: "char" },
        { name: "availability_ratio", type: "float" },
    ],
    extractProps: ({ options }) => ({ compact: !!(options && options.compact) }),
};

registry.category("fields").add("availability_semaphore", availabilitySemaphore);
