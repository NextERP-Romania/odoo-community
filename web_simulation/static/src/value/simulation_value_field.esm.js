// Copyright (C) 2026 NextERP Romania SRL
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

import {Component, useProps} from "@odoo/owl";
import {Field, getFieldFromRegistry} from "@web/views/fields/field";
import {_t} from "@web/core/l10n/translation";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";

// Which of the record's typed columns holds the value, per field type.
const FIELD_BY_TYPE = {
    char: "value_char",
    selection: "value_char",
    text: "value_text",
    integer: "value_integer",
    float: "value_float",
    monetary: "value_monetary",
    boolean: "value_boolean",
    date: "value_date",
    datetime: "value_datetime",
    many2one: "value_reference",
    many2many: "value_reference",
};

/**
 * One column that edits whatever the row happens to be.
 *
 * The row says which type it carries, and this renders the ordinary field
 * component for that type - a number for a quantity, a date picker for a
 * date, a record picker for a link - over the matching typed column. Same
 * idea core uses for properties: build the field description on the fly and
 * hand it to Field.
 */
export class SimulationValueField extends Component {
    static template = "web_simulation.SimulationValueField";
    static components = {Field};
    // Owl 3 wants the schema declared here, not as a static.
    props = useProps(standardFieldProps);

    get targetName() {
        return FIELD_BY_TYPE[this.props.record.data.ttype] || "value_char";
    }

    get fieldInfo() {
        const name = this.targetName;
        const definition = this.props.record.fields[name];
        const type = definition.type;
        const options =
            name === "value_reference"
                ? {model_field: "comodel_id", no_create: true, no_open: true}
                : {};
        return {
            name,
            type,
            widget: type,
            string: definition.string,
            options,
            attrs: {},
            context: "{}",
            help: undefined,
            readonly: "False",
            required: "False",
            invisible: "False",
            column_invisible: "False",
            onChange: false,
            forceSave: false,
            decorations: {},
            field: getFieldFromRegistry(type, type),
        };
    }
}

export const simulationValueField = {
    component: SimulationValueField,
    displayName: _t("Value of any type"),
    supportedTypes: ["char"],
};

registry.category("fields").add("simulation_value", simulationValueField);
