# Copyright (C) 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
"""Build a flow one button at a time and watch what it produces.

The wizard keeps the chain, not its result: every time a step is added the
whole flow is replayed from the start inside a savepoint and rolled back
again.  That is what lets a three-document flow - order, receipt, bill - be
put together click by click without a single row surviving it.

For a document that was never saved, the form's values travel with the
wizard and the record is rebuilt at the start of each replay.  It is cheaper
to build it again than to leave a draft behind between two clicks.
"""

import json

from odoo import api, fields, models
from odoo.exceptions import UserError


class SimulationRun(models.TransientModel):
    _name = "web.simulation.run"
    _description = "Simulate a Flow"

    model_name = fields.Char(readonly=True)
    res_id = fields.Integer(readonly=True)
    values_json = fields.Text(readonly=True)
    steps_json = fields.Text(readonly=True, default="[]")
    record_name = fields.Char(readonly=True)
    is_new = fields.Boolean(readonly=True)
    has_steps = fields.Boolean(readonly=True)

    report_id = fields.Many2one("web.simulation.result", readonly=True)
    step_ids = fields.One2many("web.simulation.run.step", "wizard_id", readonly=True)
    option_ids = fields.One2many(
        "web.simulation.run.option", "wizard_id", readonly=True
    )
    editable_ids = fields.One2many(
        "web.simulation.run.editable", "wizard_id", readonly=True
    )

    error = fields.Text(related="report_id.error")
    pending_action = fields.Char(related="report_id.pending_action")
    is_balanced = fields.Boolean(related="report_id.is_balanced")
    total_debit = fields.Float(related="report_id.total_debit")
    total_credit = fields.Float(related="report_id.total_credit")
    document_line_ids = fields.One2many(related="report_id.document_line_ids")
    move_line_ids = fields.One2many(related="report_id.move_line_ids")
    quant_line_ids = fields.One2many(related="report_id.quant_line_ids")
    account_line_ids = fields.One2many(related="report_id.account_line_ids")
    account_summary_ids = fields.One2many(related="report_id.account_summary_ids")

    # -- entry point -----------------------------------------------------

    @api.model
    def action_open(self, model_name, res_id=False, values=None):
        wizard = self.create(
            {
                "model_name": model_name,
                "res_id": res_id,
                "values_json": json.dumps(values) if not res_id else False,
                "is_new": not res_id,
            }
        )
        return wizard._replay()

    # -- the chain -------------------------------------------------------

    def _replay(self):
        """Run the chain from the start and show where it got to."""
        self.ensure_one()
        steps = json.loads(self.steps_json or "[]")
        outcome = self.env["web.simulation"].run_chain(
            self.model_name,
            self.res_id,
            json.loads(self.values_json) if self.values_json else None,
            steps,
        )
        self.step_ids.unlink()
        self.option_ids.unlink()
        self.editable_ids.unlink()
        self.write(
            {
                "record_name": outcome["subject"],
                "report_id": outcome["report_id"],
                "has_steps": bool(steps),
                "step_ids": [
                    (0, 0, {"sequence": index + 1, **step})
                    for index, step in enumerate(outcome["played"])
                ],
                "editable_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": index,
                            "label": editable["label"],
                            "parent_label": editable["parent"],
                            "model_name": editable["model"],
                            "target_json": json.dumps(editable["target"]),
                        },
                    )
                    for index, editable in enumerate(outcome["editables"])
                ],
                "option_ids": [
                    (
                        0,
                        0,
                        {
                            "sequence": index,
                            "method": option["method"],
                            "label": option["label"],
                            "document": option["document"],
                            "available": option["available"],
                            "target_json": json.dumps(option["target"]),
                        },
                    )
                    for index, option in enumerate(outcome["options"])
                ],
            }
        )
        return self._reopen()

    def _reopen(self):
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Simulate a Flow"),
            "res_model": self._name,
            "res_id": self.id,
            # An action built here, rather than read from the database, has
            # to name its views: the client maps over them as they are.
            "views": [(False, "form")],
            "view_mode": "form",
            "target": "new",
            # Three lists and a notebook do not fit a standard dialog.
            "context": {"dialog_size": "extra-large"},
        }

    def _append_step(self, target, method):
        steps = json.loads(self.steps_json or "[]")
        steps.append({"target": target, "method": method})
        self.steps_json = json.dumps(steps)
        return self._replay()

    def _append_values_step(self, target, values):
        """Record what was filled in as a step of the flow."""
        steps = json.loads(self.steps_json or "[]")
        steps.append({"target": target, "values": values})
        self.steps_json = json.dumps(steps)
        return self._replay()

    def action_undo(self):
        self.ensure_one()
        steps = json.loads(self.steps_json or "[]")
        self.steps_json = json.dumps(steps[:-1])
        return self._replay()

    def action_reset(self):
        self.ensure_one()
        self.steps_json = "[]"
        return self._replay()


class SimulationRunEditable(models.TransientModel):
    _name = "web.simulation.run.editable"
    _description = "Record the Flow Can Fill In"
    _order = "sequence, id"

    wizard_id = fields.Many2one("web.simulation.run", required=True, ondelete="cascade")
    sequence = fields.Integer(readonly=True)
    label = fields.Char(string="Record", readonly=True)
    parent_label = fields.Char(string="Part Of", readonly=True)
    model_name = fields.Char(readonly=True)
    target_json = fields.Char(readonly=True)

    def action_edit(self):
        self.ensure_one()
        return self.env["web.simulation.edit"].open_for(
            self.wizard_id,
            json.loads(self.target_json) if self.target_json else None,
        )


class SimulationRunStep(models.TransientModel):
    _name = "web.simulation.run.step"
    _description = "Simulated Step"
    _order = "sequence, id"

    wizard_id = fields.Many2one("web.simulation.run", required=True, ondelete="cascade")
    sequence = fields.Integer(readonly=True)
    label = fields.Char(string="Operation", readonly=True)
    document = fields.Char(string="On Document", readonly=True)
    method = fields.Char(readonly=True)
    failed = fields.Boolean(string="Stopped Here", readonly=True)


class SimulationRunOption(models.TransientModel):
    _name = "web.simulation.run.option"
    _description = "Possible Next Step"
    _order = "sequence, id"

    wizard_id = fields.Many2one("web.simulation.run", required=True, ondelete="cascade")
    sequence = fields.Integer(readonly=True)
    method = fields.Char(readonly=True)
    target_json = fields.Char(readonly=True)
    label = fields.Char(string="Operation", readonly=True)
    document = fields.Char(string="On Document", readonly=True)
    available = fields.Boolean(string="Available Now", readonly=True)

    def action_add(self):
        self.ensure_one()
        wizard = self.wizard_id
        if wizard.error:
            # The flow already stopped, so a new step would be recorded and
            # never reached. Say so instead of swallowing the click.
            raise UserError(
                self.env._(
                    "The flow stopped at the last step. Undo it before adding "
                    "another one."
                )
            )
        return wizard._append_step(
            json.loads(self.target_json) if self.target_json else None, self.method
        )
