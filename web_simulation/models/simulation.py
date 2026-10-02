# Copyright (C) 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
"""Run one of a document's own buttons, then take it back.

Nothing here knows about purchases, receipts or invoices.  The buttons a
document offers are written in the header of its form view, so that is where
they are read from: whatever Odoo shows you on the record is what can be
simulated, including buttons added by other modules.

The run itself is a savepoint that is always rolled back, and it lives
inside a single request, so it works on any server whatever its number of
workers.

A document that does not exist yet is handled the same way: the form's values
are sent along, the record is created inside the savepoint, the button is
pressed on it, and the rollback takes away the record together with what it
produced.  Nothing is left behind, not even a draft.
"""

import ast
import logging
from datetime import datetime

from lxml import etree

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

from ..tools import numbering
from ..tools.snapshot import take_snapshot
from ..wizard.simulation_result import DOCUMENT_MODELS, WATCHED_MODELS

_logger = logging.getLogger(__name__)

GROUP = "web_simulation.group_simulation"

#: Field types a step can set from a typed-in value.
SETTABLE_TYPES = (
    "char",
    "text",
    "integer",
    "float",
    "monetary",
    "boolean",
    "date",
    "datetime",
    "selection",
    "many2one",
    "many2many",
)


class Simulation(models.AbstractModel):
    _name = "web.simulation"
    _description = "Rolled-Back Simulation"

    # -- what can be simulated ------------------------------------------

    @api.model
    def available_actions(self, model_name, res_id):
        """List the header buttons offered by an existing record."""
        self._check_access()
        return self._actions_for(self._get_record(model_name, res_id))

    #: Views whose header or footer carries buttons that act on the record.
    #: The list view matters as much as the form: Odoo 20 moved "Create
    #: Bills" out of the purchase order form into the list header, where you
    #: tick the orders and bill them together.
    VIEW_TYPES = ("form", "list")

    @api.model
    def _header_buttons(self, model_name):
        """Every header button the model's views declare, parsed once.

        All the primary views are read, not just the default one: the
        purchase order's Create Bills button sits on a list view that is not
        the one Odoo opens by default, and a button you can reach somewhere
        in the interface is a step the flow can take.
        """
        key = ("web_simulation.header_buttons", model_name)
        cached = self.env.cr.cache.get(key)
        if cached is not None:
            return cached

        model = self.env[model_name]
        views = (
            self.env["ir.ui.view"]
            .sudo()
            .search(
                [
                    ("model", "=", model_name),
                    ("type", "in", self.VIEW_TYPES),
                    ("mode", "=", "primary"),
                ]
            )
        )
        buttons = []
        seen = set()
        for view_id, view_type in [(None, "form"), (None, "list")] + [
            (view.id, view.type) for view in views
        ]:
            try:
                arch = etree.fromstring(
                    model.get_view(view_id=view_id, view_type=view_type)["arch"]
                )
            except Exception:
                # A model without that view, or a view that cannot be built
                # for this user, simply offers nothing.
                continue
            # Documents keep their buttons in the header; dialogs, which is
            # what a flow runs into when Odoo asks something, keep them in
            # the footer.
            nodes = arch.xpath("//header//button[@type='object'][@name]")
            nodes += arch.xpath("//footer//button[@type='object'][@name]")
            for button in nodes:
                method = button.get("name")
                if method.startswith("_") or not method.isidentifier():
                    continue
                spec = (
                    method,
                    button.get("string") or button.get("title") or "",
                    button.get("invisible") or "",
                    button.get("groups") or "",
                )
                if spec in seen:
                    continue
                seen.add(spec)
                buttons.append(
                    {
                        "method": method,
                        "label": spec[1] or method.replace("_", " "),
                        "invisible": spec[2],
                        "groups": spec[3],
                    }
                )
        self.env.cr.cache[key] = buttons
        return buttons

    @api.model
    def _actions_for(self, record):
        """What the record's buttons offer, and which of them apply now.

        Buttons hidden by the view are still listed, greyed out, because
        "why can I not do this yet" is a question worth answering too.
        """
        # The same button is often written several times, each copy visible
        # in a different situation - account.move carries two Post buttons,
        # one for entries and one for invoices.  They are one action,
        # available when any of the copies is shown.
        actions = {}
        for button in self._header_buttons(record._name):
            if not self._groups_allow(button["groups"]):
                continue
            available = self._is_available(button["invisible"], record)
            action = actions.get(button["method"])
            if action is None:
                actions[button["method"]] = {
                    "method": button["method"],
                    "label": button["label"],
                    "available": available,
                }
            elif available and not action["available"]:
                # Prefer the wording of the copy that is actually shown.
                action["available"] = True
                action["label"] = button["label"]
        return list(actions.values())

    @api.model
    def _groups_allow(self, groups):
        if not groups:
            return True
        return any(
            self.env.user.has_group(group.strip())
            for group in groups.split(",")
            if group.strip() and not group.strip().startswith("!")
        )

    @api.model
    def _is_available(self, expression, record):
        """Evaluate a view's ``invisible`` against the record.

        Best effort on purpose: these expressions are meant for the browser,
        which knows more than we do here.  When one cannot be evaluated the
        button is offered anyway - showing one button too many is cheaper
        than hiding the one that was wanted, and a wrong choice costs
        nothing since the run is rolled back.
        """
        if not expression:
            return True
        if expression in ("1", "True"):
            return False
        if expression in ("0", "False"):
            return True
        try:
            names = {
                node.id
                for node in ast.walk(ast.parse(expression, mode="eval"))
                if isinstance(node, ast.Name)
            }
            values = {"id": record.id, "uid": self.env.uid}
            values["context"] = dict(self.env.context)
            for name in names:
                field = record._fields.get(name)
                if field is None:
                    continue
                value = record[name]
                if isinstance(value, models.BaseModel):
                    value = (
                        value.ids
                        if field.type in ("one2many", "many2many")
                        else value.id
                    )
                values[name] = value
            return not safe_eval(expression, values)
        except Exception:
            _logger.debug("Cannot evaluate %r on %s", expression, record, exc_info=True)
            return True

    # -- running it ------------------------------------------------------

    @api.model
    def run_chain(self, model_name, res_id, values, steps):
        """Play a whole flow, then take it all back.

        The steps are replayed from the start every time, which is why no
        transaction has to stay open between requests: the chain is the
        recipe, not the state.  Buying, receiving and invoicing is three
        steps on three documents, and the second and third documents are the
        ones the earlier steps produced.

        Returns the report, the chain as it ran, and what could come next.
        """
        self._check_access()
        Report = self.env["web.simulation.result"]
        cr = self.env.cr
        snapshot = take_snapshot(cr, self.env.registry, WATCHED_MODELS)
        data = {"documents": [], "moves": [], "quants": []}
        played = []
        options = []
        editables = []
        pending = None
        subject = ""
        refused = None
        # Replaying a flow must not eat an order number per click.
        with numbering.own_numbering():
            savepoint = cr.savepoint(flush=True)
            try:
                origin = self._subject(model_name, res_id, values)
                subject = origin.display_name
                wizards = {}
                for index, step in enumerate(steps):
                    target = self._resolve_target(
                        origin, snapshot, step.get("target"), wizards
                    )
                    if step.get("method"):
                        label = self._label_of(target, step["method"])
                    else:
                        label = self._values_label(target, step.get("values") or {})
                    played.append(
                        {
                            "label": label,
                            "document": self._name_of(target),
                            "method": step.get("method") or "",
                        }
                    )
                    # Each step gets a savepoint of its own so that a step
                    # that fails does not take the earlier ones with it: the
                    # report then still shows what the flow managed to do
                    # before it hit the wall.
                    step_point = cr.savepoint(flush=True)
                    try:
                        if step.get("method"):
                            result = getattr(target, step["method"])()
                        else:
                            target.write(
                                self._convert(target, step.get("values") or {})
                            )
                            result = None
                        cr.flush()
                    except (UserError, ValidationError) as failure:
                        step_point.close(rollback=True)
                        self.env.invalidate_all()
                        played[-1]["failed"] = True
                        data["error"] = str(failure)
                        break
                    step_point.close(rollback=False)
                    if (step.get("target") or {}).get("wizard_of") is not None:
                        # This step answered the dialog, so it is no longer
                        # in the way.
                        pending = None
                        data["pending_action"] = False
                    asked = self._question_asked(result)
                    if asked:
                        # Odoo wants an answer before doing the work: create
                        # the backorder or not, pick the lots.  The dialog it
                        # opened is a record like any other, so it is kept as
                        # a target and its own buttons become the next steps.
                        wizards[index] = asked["record"]
                        pending = {"index": index, "record": asked["record"]}
                        data["pending_action"] = asked["name"]
                data.update(Report._collect(snapshot))
                options = self._next_options(origin, snapshot, pending)
                editables = self._editables(origin, snapshot, pending)
            except AccessError as error:
                # Re-raised once the savepoint is gone: a refusal is not a result.
                refused = error
            except UserError as error:
                data["error"] = str(error)
            except Exception as error:  # noqa: BLE001 - shown, not swallowed
                _logger.info(
                    "Simulation on %s,%s failed", model_name, res_id, exc_info=True
                )
                data["error"] = str(error)
            finally:
                savepoint.close(rollback=True)
                # The cache still describes rows that are gone, and the
                # after-commit hooks queued by the run must never fire: they are
                # the ones that send mail and call out to other systems.
                self.env.invalidate_all()
                cr.postcommit.clear()
        if refused is not None:
            raise refused

        data["can_open"] = False
        data["origin_label"] = self.env._("Simulation on %(record)s", record=subject)
        return {
            "report_id": Report._materialize(data).id,
            "subject": subject,
            "played": played,
            "options": options,
            "editables": editables,
        }

    @api.model
    def _subject(self, model_name, res_id, values):
        """The record the flow starts from, existing or built on the spot."""
        if res_id:
            record = self._get_record(model_name, res_id)
            record.check_access("write")
            return record
        if not values:
            raise UserError(self.env._("Neither a document nor values to simulate."))
        self.env[model_name].check_access("create")
        return self.env[model_name].create(values)

    @api.model
    def _label_of(self, record, method):
        """Name the button, and refuse anything that is not one.

        The header of the form view is the boundary: without this check the
        route would call any method of any model.
        """
        for action in self._actions_for(record):
            if action["method"] == method:
                return action["label"]
        raise AccessError(
            self.env._("%(method)s is not a button of this document.", method=method)
        )

    @api.model
    def _question_asked(self, result):
        """Name the wizard a button put in the way, if it did.

        Buttons return actions for two different reasons.  Some ask
        something before doing the work - confirm the backorder, pick the
        lots - and the work has not happened.  Others have done the work and
        are showing you the result, the way Create Bills opens the bill it
        just made.  What tells them apart is that a question is a transient
        record opened in a dialog; that record is returned here so the flow
        can go on to answer it.
        """
        if not isinstance(result, dict):
            return None
        if result.get("type") != "ir.actions.act_window":
            return None
        model_name = result.get("res_model")
        if not model_name or model_name not in self.env:
            return None
        if result.get("target") != "new" or not self.env[model_name]._transient:
            return None
        res_id = result.get("res_id")
        if res_id:
            record = self.env[model_name].browse(res_id)
        else:
            # Most of these dialogs hand the client a model and a context
            # and let it build the record.  Nobody is watching here, so it
            # is built the same way, from the same defaults.
            context = result.get("context")
            if isinstance(context, str):
                try:
                    context = safe_eval(context, {"uid": self.env.uid})
                except Exception:
                    context = {}
            try:
                record = self.env[model_name].with_context(**(context or {})).create({})
            except Exception:
                _logger.info(
                    "Cannot build the %s dialog to answer it", model_name, exc_info=True
                )
                return None
        return {
            "name": result.get("name") or model_name,
            "record": record,
        }

    # -- following the documents the flow creates -------------------------

    @api.model
    def _created(self, snapshot):
        """Documents created so far, per model, in the order they appeared.

        Ids come from sequences, so ordering by id is the order of creation,
        and a replay of the same chain produces the same order.  That is what
        makes a step able to say "the first receipt" and mean it again next
        time.
        """
        created = {}
        for model_name in DOCUMENT_MODELS:
            mark = snapshot.get(model_name)
            if mark is None or model_name not in self.env:
                continue
            records = (
                self.env[model_name]
                .sudo()
                .with_context(active_test=False)
                .search([("id", ">", mark)], order="id")
            )
            if records:
                created[model_name] = records
        return created

    @api.model
    def _resolve_target(self, origin, snapshot, target, wizards=None):
        """Find the record a step acts on.

        A target is either the document the flow started from, one of the
        documents it created, or - and this is what makes line editing work
        - a record reached from one of those through a one2many, named by
        the field and the position in it.  Positions are stable because a
        replay of the same chain produces the same records in the same
        order.
        """
        if not target:
            return origin
        record = origin
        if target.get("wizard_of") is not None:
            record = (wizards or {}).get(target["wizard_of"])
            if record is None:
                raise UserError(
                    self.env._(
                        "The step answers a question that step %(step)s no "
                        "longer asks.",
                        step=target["wizard_of"] + 1,
                    )
                )
        elif target.get("model"):
            records = self._created(snapshot).get(target["model"])
            index = target.get("index", 0)
            if not records or index >= len(records):
                raise UserError(
                    self.env._(
                        "The step asks for %(model)s number %(index)s, but "
                        "the flow did not produce it.",
                        model=target["model"],
                        index=index + 1,
                    )
                )
            record = records[index]
        for hop in target.get("path", []):
            children = record[hop["field"]]
            index = hop.get("index", 0)
            if index >= len(children):
                raise UserError(
                    self.env._(
                        "The step asks for line %(index)s of %(field)s on "
                        "%(record)s, which is not there.",
                        index=index + 1,
                        field=hop["field"],
                        record=record.display_name,
                    )
                )
            record = children[index]
        return record

    @api.model
    def inspect(self, model_name, res_id, values, steps, target):
        """Replay the chain and describe one record, so it can be filled in.

        The record only exists during a replay, so this is the only moment
        its current values can be read.  They come back as text, which is
        what the person then edits.
        """
        self._check_access()
        cr = self.env.cr
        snapshot = take_snapshot(cr, self.env.registry, WATCHED_MODELS)
        described = {"label": "", "model": "", "fields": []}
        with numbering.own_numbering():
            savepoint = cr.savepoint(flush=True)
            try:
                origin = self._subject(model_name, res_id, values)
                wizards = {}
                for index, step in enumerate(steps):
                    played_on = self._resolve_target(
                        origin, snapshot, step.get("target"), wizards
                    )
                    point = cr.savepoint(flush=True)
                    try:
                        if step.get("method"):
                            result = getattr(played_on, step["method"])()
                        else:
                            played_on.write(
                                self._convert(played_on, step.get("values") or {})
                            )
                            result = None
                        cr.flush()
                    except (UserError, ValidationError):
                        # A step that does not go through leaves the record
                        # as it was; describing that is still useful.
                        point.close(rollback=True)
                        self.env.invalidate_all()
                        break
                    point.close(rollback=False)
                    asked = self._question_asked(result)
                    if asked:
                        wizards[index] = asked["record"]
                record = self._resolve_target(origin, snapshot, target, wizards)
                described["label"] = self._name_of(record)
                described["model"] = record._name
                described["fields"] = self._describe(record)
            finally:
                savepoint.close(rollback=True)
                self.env.invalidate_all()
                cr.postcommit.clear()
        return described

    @api.model
    def _describe(self, record):
        """Each field of the record: what it is, what it holds right now.

        The value comes back twice - once to read and once to edit - and the
        editable one is shaped so json can carry it to the wizard and back.
        """
        described = []
        for name in self.editable_fields(record._name):
            field = record._fields[name]
            value = record[name]
            described.append(
                {
                    "name": name,
                    "label": field.string,
                    "ttype": field.type,
                    "current": self._shown(field, value),
                    "value": self._editable(field, value),
                    "comodel": field.comodel_name if field.relational else "",
                    "options": ", ".join(
                        code for code, _label in (field.selection or [])
                    )
                    if field.type == "selection" and isinstance(field.selection, list)
                    else "",
                    "currency_id": record[field.currency_field].id
                    if field.type == "monetary"
                    and getattr(field, "currency_field", None)
                    and field.currency_field in record._fields
                    else False,
                }
            )
        return described

    @api.model
    def _shown(self, field, value):
        """The value as a person reads it."""
        if field.type == "many2one":
            return value.display_name or ""
        if field.type == "many2many":
            return ", ".join(value.mapped("display_name"))
        if field.type == "boolean":
            return "1" if value else "0"
        if value in (False, None):
            return ""
        return str(value)

    @api.model
    def _editable(self, field, value):
        """The value as json can carry it."""
        if field.type == "many2one":
            return value.id or False
        if field.type == "many2many":
            return value.ids
        if field.type == "date":
            return fields.Date.to_string(value) if value else False
        if field.type == "datetime":
            return fields.Datetime.to_string(value) if value else False
        if field.type in ("integer", "float", "monetary"):
            return value or 0
        if field.type == "boolean":
            return bool(value)
        return value or ""

    # -- what can be filled in -------------------------------------------

    @api.model
    def _editables(self, origin, snapshot, pending=None):
        """The records whose values a step can set.

        Every document the flow touched, plus the lines under it: without
        the lines there would be no way to receive three of ten, which is
        half of what one wants to try out.
        """
        editables = []
        seen = set()
        documents = [(None, origin)]
        if pending:
            documents.append(({"wizard_of": pending["index"]}, pending["record"]))
        for model_name, records in self._created(snapshot).items():
            for index, record in enumerate(records):
                if record != origin:
                    documents.append(({"model": model_name, "index": index}, record))
        for target, record in documents:
            editables.append(
                {
                    "target": target,
                    "model": record._name,
                    "label": self._name_of(record),
                    "parent": "",
                }
            )
            editables.extend(self._editable_lines(target, record, seen))
        return editables

    @api.model
    def _editable_lines(self, target, record, seen):
        """One level down: the lines shown on the record's own form.

        A bill shows the same rows through ``invoice_line_ids`` and again
        through ``line_ids``; whichever the form names first wins, so the
        list stays the length of the document rather than twice that.
        """
        lines = []
        for field_name in self._line_fields(record._name):
            field = record._fields.get(field_name)
            if field is None or field.type != "one2many":
                continue
            for index, child in enumerate(record[field_name]):
                if (child._name, child.id) in seen:
                    continue
                seen.add((child._name, child.id))
                lines.append(
                    {
                        "target": {
                            **(target or {}),
                            "path": [{"field": field_name, "index": index}],
                        },
                        "model": child._name,
                        "label": child.display_name
                        or self._fallback_label(child, index),
                        "parent": f"{record.display_name} / {field.string}",
                    }
                )
        return lines

    @api.model
    def _name_of(self, record):
        """What to call a record on screen.

        A dialog has no name of its own, and "stock.backorder.confirmation,4"
        tells nobody anything; its model reads better.
        """
        name = record.display_name or ""
        if not name or name.startswith(record._name + ","):
            return self.env["ir.model"]._get(record._name).name
        return name

    @api.model
    def _fallback_label(self, record, index):
        """Name a line that has no display name of its own."""
        return f"{self.env['ir.model']._get(record._name).name} #{index + 1}"

    @api.model
    def _line_fields(self, model_name):
        """One2many fields the model's form view actually shows."""
        key = ("web_simulation.line_fields", model_name)
        cached = self.env.cr.cache.get(key)
        if cached is not None:
            return cached
        names = []
        try:
            arch = etree.fromstring(
                self.env[model_name].get_view(view_type="form")["arch"]
            )
        except Exception:
            arch = None
        if arch is not None:
            model = self.env[model_name]
            for node in arch.xpath("//field[@name]"):
                name = node.get("name")
                field = model._fields.get(name)
                if field is not None and field.type == "one2many" and name not in names:
                    names.append(name)
        self.env.cr.cache[key] = names
        return names

    @api.model
    def editable_fields(self, model_name):
        """Fields of ``model_name`` a step may set.

        Taken from the model's own views, so the offer stays close to what
        the interface lets a person change, and filtered to the stored,
        writable, single-valued ones - the kind that can be typed in.
        """
        key = ("web_simulation.editable_fields", model_name)
        cached = self.env.cr.cache.get(key)
        if cached is not None:
            return cached
        names = set()
        for view_type in self.VIEW_TYPES:
            try:
                arch = etree.fromstring(
                    self.env[model_name].get_view(view_type=view_type)["arch"]
                )
            except Exception:
                continue
            for node in arch.xpath("//field[@name]"):
                names.add(node.get("name"))
        model = self.env[model_name]
        fields = []
        for name in sorted(names):
            field = model._fields.get(name)
            if field is None or field.type not in SETTABLE_TYPES:
                continue
            if not field.store or field.readonly:
                # A stored computed field that is not readonly is meant to
                # be overridden - the taxes on an invoice line are one -
                # so ``readonly`` is the test, not ``compute``.
                continue
            fields.append(name)
        self.env.cr.cache[key] = fields
        return fields

    @api.model
    def _values_label(self, record, values):
        parts = []
        for name, value in values.items():
            field = record._fields.get(name)
            label = field.string if field else name
            parts.append(f"{label} = {self._value_label(field, value)}")
        return self.env._("Set %s", ", ".join(parts))

    @api.model
    def _value_label(self, field, value):
        """Say what a value is, not how it is stored."""
        if field is None:
            return value
        if field.type == "many2many" and isinstance(value, dict):
            picked = value.get("id")
            name = (
                self.env[field.comodel_name].browse(picked).display_name
                if picked
                else self.env._("nothing")
            )
            operation = value.get("operation") or "add"
            if operation == "remove":
                return self.env._("without %s", name)
            if operation == "only":
                return self.env._("only %s", name)
            return self.env._("plus %s", name)
        if field.type == "many2one" and value:
            return self.env[field.comodel_name].browse(int(value)).display_name
        if field.type == "boolean":
            return self.env._("yes") if value else self.env._("no")
        return value

    @api.model
    def _convert(self, record, values):
        """Turn what was typed into what the field expects."""
        converted = {}
        for name, raw in values.items():
            field = record._fields.get(name)
            if field is None:
                continue
            if field.type == "many2many":
                converted[name] = self._many2many_command(raw)
            elif raw in (None, "") and field.type not in ("char", "text"):
                converted[name] = False
            elif field.type in ("integer",):
                converted[name] = int(float(raw))
            elif field.type in ("float", "monetary"):
                converted[name] = float(raw)
            elif field.type == "boolean":
                converted[name] = str(raw).strip().lower() in (
                    "1",
                    "true",
                    "yes",
                    "da",
                    "x",
                )
            elif field.type == "many2one":
                if str(raw).isdigit():
                    converted[name] = int(raw)
                else:
                    found = self.env[field.comodel_name].name_search(str(raw), limit=1)
                    if not found:
                        raise UserError(
                            self.env._(
                                "No %(model)s found for %(value)s.",
                                model=field.comodel_name,
                                value=raw,
                            )
                        )
                    converted[name] = found[0][0]
            elif field.type in ("date", "datetime"):
                converted[name] = self._to_date(field, raw)
            else:
                converted[name] = raw
        return converted

    @api.model
    def _many2many_command(self, raw):
        """Add one record to a list of records, take one out, or replace it."""
        if not isinstance(raw, dict):
            ids = raw if isinstance(raw, list) else [raw]
            return [Command.set([int(one) for one in ids if one])]
        res_id = raw.get("id")
        if not res_id:
            return [Command.clear()]
        operation = raw.get("operation") or "add"
        if operation == "remove":
            return [Command.unlink(int(res_id))]
        if operation == "only":
            return [Command.set([int(res_id)])]
        return [Command.link(int(res_id))]

    @api.model
    def _to_date(self, field, raw):
        """Accept a date the way it is written on screen, not only ISO."""
        raw = str(raw).strip()
        lang = self.env["res.lang"]._lang_get(self.env.user.lang or "en_US")
        patterns = ["%Y-%m-%d", lang.date_format]
        if field.type == "datetime":
            patterns = [
                "%Y-%m-%d %H:%M:%S",
                f"{lang.date_format} {lang.time_format}",
                "%Y-%m-%d",
                lang.date_format,
            ]
        for pattern in patterns:
            try:
                parsed = datetime.strptime(raw, pattern)
            except ValueError:
                continue
            return parsed.date() if field.type == "date" else parsed
        raise UserError(self.env._("%(value)s is not a date I can read.", value=raw))

    @api.model
    def _next_options(self, origin, snapshot, pending=None):
        """What can be done next, on the origin and on what the flow made.

        When the flow is sitting on a dialog, that dialog's own buttons come
        first: answering it is the only way forward.
        """
        options = []
        documents = []
        if pending:
            documents.append(({"wizard_of": pending["index"]}, pending["record"]))
        documents.append((None, origin))
        for model_name, records in self._created(snapshot).items():
            for index, record in enumerate(records):
                if record == origin:
                    continue
                documents.append(({"model": model_name, "index": index}, record))
        for target, record in documents:
            for action in self._actions_for(record):
                if not action["available"]:
                    # Listing what cannot be done turns the dialog into a
                    # wall of forty buttons; the state of the flow already
                    # says why something is missing.
                    continue
                options.append(
                    {
                        "target": target,
                        "method": action["method"],
                        "label": action["label"],
                        "document": self._name_of(record),
                        "available": True,
                    }
                )
        return options

    # -- helpers ----------------------------------------------------------

    @api.model
    def _check_access(self):
        if not self.env.user.has_group(GROUP):
            raise AccessError(self.env._("You are not allowed to simulate operations."))

    @api.model
    def _get_record(self, model_name, res_id):
        if model_name not in self.env:
            raise UserError(self.env._("Model %s does not exist.", model_name))
        record = self.env[model_name].browse(res_id)
        if not record.exists():
            raise UserError(self.env._("The document no longer exists."))
        record.check_access("read")
        return record
