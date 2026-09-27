# Copyright (C) 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
"""Fill in a document the flow created.

The record exists only while the flow is being replayed, so it cannot be
opened the way a saved one would be.  What is opened instead is the list of
its fields with their current values; whatever gets changed here becomes a
step of the flow, applied again on every replay just before the next button
is pressed.

Each field is edited with the widget of its own type - a quantity as a
number, an amount with its currency, a date in a date picker, a link with a
record picker - because a value typed into a text box is a value nobody can
check until the flow runs.
"""

import json

from odoo import api, fields, models
from odoo.exceptions import UserError


class SimulationEdit(models.TransientModel):
    _name = "web.simulation.edit"
    _description = "Fill In a Simulated Record"

    run_id = fields.Many2one("web.simulation.run", required=True, ondelete="cascade")
    target_json = fields.Char(readonly=True)
    record_label = fields.Char(readonly=True)
    model_label = fields.Char(readonly=True)
    field_ids = fields.One2many("web.simulation.edit.field", "edit_id")

    # Two columns only make sense for some rows: the allowed values of a
    # selection, and what to do with a picked record in a list of records.
    has_selection = fields.Boolean(compute="_compute_has")
    has_many2many = fields.Boolean(compute="_compute_has")

    @api.depends("field_ids.ttype")
    def _compute_has(self):
        for editor in self:
            types = set(editor.field_ids.mapped("ttype"))
            editor.has_selection = "selection" in types
            editor.has_many2many = "many2many" in types

    @api.model
    def open_for(self, run, target):
        described = self.env["web.simulation"].inspect(
            run.model_name,
            run.res_id,
            json.loads(run.values_json) if run.values_json else None,
            json.loads(run.steps_json or "[]"),
            target,
        )
        editor = self.create(
            {
                "run_id": run.id,
                "target_json": json.dumps(target),
                "record_label": described["label"],
                "model_label": described["model"],
                "field_ids": [
                    (0, 0, self._line_values(index, field))
                    for index, field in enumerate(described["fields"])
                ],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Fill In"),
            "res_model": self._name,
            "res_id": editor.id,
            "views": [(False, "form")],
            "view_mode": "form",
            "target": "new",
            "context": {"dialog_size": "extra-large"},
        }

    @api.model
    def _line_values(self, index, field):
        """One row, with its current value already in the right box."""
        ttype = field["ttype"]
        values = {
            "sequence": index,
            "name": field["name"],
            "label": field["label"],
            "ttype": ttype,
            "current": field["current"],
            "selection_hint": field.get("options") or "",
        }
        if field.get("comodel"):
            values["comodel_id"] = (
                self.env["ir.model"]._get_id(field["comodel"]) or False
            )
        if field.get("currency_id"):
            values["currency_id"] = field["currency_id"]
        value = field.get("value")
        if value in (None, False) and ttype != "boolean":
            return values
        if ttype in ("char", "selection"):
            values["value_char"] = value
        elif ttype == "text":
            values["value_text"] = value
        elif ttype == "integer":
            values["value_integer"] = value
        elif ttype == "float":
            values["value_float"] = value
        elif ttype == "monetary":
            values["value_monetary"] = value
        elif ttype == "boolean":
            values["value_boolean"] = bool(value)
        elif ttype == "date":
            values["value_date"] = value
        elif ttype == "datetime":
            values["value_datetime"] = value
        # Links are not pre-filled: the record a flow just made is gone by
        # the time this is rendered, and the current value is in its own
        # column anyway.  The picker starts empty, which is what it is for.
        return values

    def action_apply(self):
        self.ensure_one()
        values = {}
        for line in self.field_ids.filtered("change"):
            values[line.name] = line._step_value()
        if not values:
            raise UserError(
                self.env._("Tick Change on the values you want the flow to set.")
            )
        return self.run_id._append_values_step(
            json.loads(self.target_json) if self.target_json else None, values
        )


class SimulationEditField(models.TransientModel):
    _name = "web.simulation.edit.field"
    _description = "Field of a Simulated Record"
    _order = "sequence, id"

    edit_id = fields.Many2one("web.simulation.edit", required=True, ondelete="cascade")
    sequence = fields.Integer(readonly=True)
    name = fields.Char(string="Technical Name", readonly=True)
    label = fields.Char(string="Field", readonly=True)
    ttype = fields.Char(string="Type", readonly=True)
    current = fields.Char(string="Current Value", readonly=True)
    change = fields.Boolean(help="Only the ticked values are set by the flow.")
    comodel_id = fields.Many2one("ir.model", readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)
    selection_hint = fields.Char(string="Allowed Values", readonly=True)

    value_char = fields.Char(string="Text")
    value_text = fields.Text(string="Long Text")
    value_integer = fields.Integer(string="Whole Number")
    value_float = fields.Float(string="Decimal")
    value_monetary = fields.Monetary(string="Amount", currency_field="currency_id")
    value_boolean = fields.Boolean(string="Yes / No")
    value_date = fields.Date(string="Date")
    value_datetime = fields.Datetime(string="Date & Time")
    value_reference = fields.Reference(selection="_selection_models", string="Record")
    many2many_operation = fields.Selection(
        [("add", "Add"), ("remove", "Remove"), ("only", "Only this")],
        string="How",
        default="add",
        help="What to do with the picked record in a list of records.",
    )

    @api.model
    def _selection_models(self):
        """Every model, the way core does it for reference fields.

        The row's own ``comodel_id`` narrows it down in the view, so the
        person only picks a record, never a model.
        """
        return [
            (model.model, model.name)
            for model in self.env["ir.model"].sudo().search([])
        ]

    def _step_value(self):
        """What goes into the step, in a shape json can carry."""
        self.ensure_one()
        if self.ttype in ("char", "selection"):
            return self.value_char or ""
        if self.ttype == "text":
            return self.value_text or ""
        if self.ttype == "integer":
            return self.value_integer
        if self.ttype == "float":
            return self.value_float
        if self.ttype == "monetary":
            return self.value_monetary
        if self.ttype == "boolean":
            return self.value_boolean
        if self.ttype == "date":
            return fields.Date.to_string(self.value_date)
        if self.ttype == "datetime":
            return fields.Datetime.to_string(self.value_datetime)
        if self.ttype == "many2one":
            return self.value_reference.id if self.value_reference else False
        if self.ttype == "many2many":
            return {
                "operation": self.many2many_operation or "add",
                "id": self.value_reference.id if self.value_reference else False,
            }
        return self.value_char or ""
