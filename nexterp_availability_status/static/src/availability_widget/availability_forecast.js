/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ForecastWidgetField, forecastWidgetField } from "@stock/widgets/forecast_widget";

// Same colour mapping as the standalone semaphore.
const COLOR = {
    available: "available",
    partial: "partial",
    to_transfer: "split",
    mo_late: "split",
    reception: "waiting",
    production: "waiting",
    to_order: "unavailable",
    to_manufacture: "unavailable",
    po_draft: "unavailable",
    mo_draft: "unavailable",
    unavailable: "unavailable",
};

/**
 * Drop-in replacement for stock's `forecast_widget`: instead of a second
 * column, it renders our traffic-light dot (colour by availability_status_code,
 * status text on hover) while keeping the native "open forecast report" button.
 */
export class AvailabilityForecastField extends ForecastWidgetField {
    static template = "nexterp_availability_status.AvailabilityForecast";

    get code() {
        return this.props.record.data.availability_status_code || "none";
    }

    get color() {
        return COLOR[this.code] || "none";
    }

    get statusLabel() {
        return this.props.record.data.availability_status_label || "";
    }

    get statusRatio() {
        const r = this.props.record.data.availability_ratio || 0;
        return Math.max(0, Math.min(1, r));
    }

    // The forecast cell is a right-aligned numeric cell whose styling zeroes a
    // plain dot, so build the dot entirely from inline styles here.
    get dotStyle() {
        const GREEN = "#28a745";
        const AMBER = "#f0ad4e";
        const RED = "#dc3545";
        const EMPTY = "#d1d5db";
        let background;
        if (this.color === "split") {
            background = `linear-gradient(to right, ${AMBER} 50%, ${GREEN} 50%)`;
        } else if (this.color === "partial") {
            const pct = Math.round(this.statusRatio * 100);
            background = `linear-gradient(to right, ${GREEN} ${pct}%, ${EMPTY} ${pct}%)`;
        } else {
            background = { available: GREEN, waiting: AMBER, unavailable: RED }[this.color] || EMPTY;
        }
        return (
            "display:inline-block;width:12px;height:12px;border-radius:50%;" +
            "vertical-align:middle;box-shadow:inset 0 0 0 1px rgba(0,0,0,0.15);" +
            `background:${background};`
        );
    }
}

export const availabilityForecastField = {
    ...forecastWidgetField,
    component: AvailabilityForecastField,
    fieldDependencies: [
        ...(forecastWidgetField.fieldDependencies || []),
        { name: "availability_status_code", type: "selection" },
        { name: "availability_status_label", type: "char" },
        { name: "availability_ratio", type: "float" },
    ],
};

registry.category("fields").add("availability_forecast", availabilityForecastField);
