# Copyright 2026 NextERP Romania
# License LGPL-3
"""Per-partner rules telling which CIUS-RO XML node gets which value."""

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import datetime as safe_datetime
from odoo.tools.safe_eval import safe_eval

from odoo.addons.account_edi_ubl_cii.tools.ubl_21_credit_note import (
    CreditNote,
    CreditNoteLine,
)
from odoo.addons.account_edi_ubl_cii.tools.ubl_21_invoice import Invoice, InvoiceLine

from ..tools.ciusro_fields import CIUSRO_FIELDS, CUSTOM_KEY, get_selection

# The UBL templates a path is validated against, per scope. 'dict_to_xml'
# raises a ValueError on any tag missing from them, so a path that is not in
# both templates of its scope would break the export at send time.
TEMPLATES = {
    "document": {"invoice": Invoice, "credit_note": CreditNote},
    "line": {"invoice": InvoiceLine, "credit_note": CreditNoteLine},
}

VALUE_TYPES = [
    ("field", "Field"),
    ("fixed", "Fixed text"),
    ("expression", "Python expression"),
    ("remove", "Remove the node"),
]

DOCUMENT_TYPES = [
    ("all", "Invoices and credit notes"),
    ("invoice", "Invoices only"),
    ("credit_note", "Credit notes only"),
]


class L10nRoEdiXmlRule(models.Model):
    _name = "l10n_ro.edi.xml.rule"
    _description = "CIUS-RO XML field rule"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    profile_id = fields.Many2one(
        comodel_name="l10n_ro.edi.xml.profile",
        string="Profile",
        ondelete="cascade",
        index="btree_not_null",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        ondelete="cascade",
        index="btree_not_null",
        help="Rule defined directly on a partner. It takes precedence over a "
        "rule of the partner's profile writing the same node.",
    )

    field_key = fields.Selection(
        selection=lambda self: get_selection() + [(CUSTOM_KEY, "Custom path")],
        string="XML field",
        required=True,
        help="The CIUS-RO node to fill. Pick 'Custom path' to address a node "
        "the catalog does not list yet.",
    )
    field_help = fields.Char(compute="_compute_field_help")
    scope = fields.Selection(
        selection=[("document", "Document"), ("line", "Invoice line")],
        compute="_compute_from_field_key",
        store=True,
        readonly=False,
        precompute=True,
        required=True,
        help="Whether the node sits on the invoice root or is repeated on "
        "every invoice line.",
    )
    xml_path = fields.Char(
        string="XML path",
        compute="_compute_from_field_key",
        store=True,
        readonly=False,
        precompute=True,
        required=True,
        help="Slash separated UBL tags, relative to the Invoice/CreditNote "
        "root (or to the line, for a line rule), e.g. "
        "cac:OrderReference/cbc:ID.",
    )
    attribute = fields.Char(
        compute="_compute_from_field_key",
        store=True,
        readonly=False,
        precompute=True,
        help="Write the value in this XML attribute instead of the node text, "
        "e.g. schemeID.",
    )
    max_len = fields.Integer(
        string="Max. length",
        compute="_compute_from_field_key",
        store=True,
        readonly=False,
        precompute=True,
        help="The value is truncated to this many characters, as the ANAF "
        "schematron requires. 0 means no limit.",
    )

    value_type = fields.Selection(
        selection=VALUE_TYPES,
        string="Value from",
        required=True,
        default="field",
    )
    field_path = fields.Char(
        string="Field",
        help="Dotted path read on the invoice (or on the invoice line, for a "
        "line rule), e.g. partner_shipping_id.ref. A chain ending on several "
        "records is joined with commas.",
    )
    value_fixed = fields.Char(string="Fixed value")
    expression = fields.Text(
        help="Python expression returning the value. Available names: record "
        "(the invoice or the invoice line), move, line, partner, env, "
        "datetime. Example: move.picking_ids[:1].name",
    )

    document_types = fields.Selection(
        selection=DOCUMENT_TYPES,
        string="Applies to",
        compute="_compute_from_field_key",
        store=True,
        readonly=False,
        precompute=True,
        required=True,
        help="Some UBL nodes only exist on one of the two documents; for "
        "those, the catalog narrows this down on its own.",
    )
    overwrite = fields.Boolean(
        default=True,
        help="Uncheck to fill the node only when Odoo left it empty, instead "
        "of replacing what Odoo computed.",
    )
    value_required = fields.Boolean(
        string="Required",
        help="Block the export with an explicit error when this rule produces "
        "no value, instead of silently leaving the node out.",
    )
    note = fields.Char(string="Reason", help="Why this partner needs the rule.")

    # ------------------------------------------------------------------
    # Compute / constraints
    # ------------------------------------------------------------------

    @api.depends("field_key")
    def _compute_from_field_key(self):
        # These fields are computed from 'field_key' alone, never from their
        # own value: reading a field inside the compute that produces it is
        # what makes such "keep what is there" computes recurse on new records.
        # They stay editable, and picking another field in the catalog resets
        # them to that field's definition, which is what the user asked for.
        for rule in self:
            entry = CIUSRO_FIELDS.get(rule.field_key)
            if not entry:
                # Custom path: the user fills it in by hand.
                rule.scope = "document"
                rule.xml_path = False
                rule.attribute = False
                rule.max_len = 0
                rule.document_types = "all"
                continue
            rule.scope = entry["scope"]
            rule.xml_path = "/".join(entry["path"])
            rule.attribute = entry.get("attribute", False)
            rule.max_len = entry.get("max_len", 0)
            doc_types = entry.get("doc_types")
            # A node UBL only defines on one document type cannot apply to both.
            rule.document_types = (
                doc_types[0] if doc_types and len(doc_types) == 1 else "all"
            )

    @api.depends("field_key")
    def _compute_field_help(self):
        for rule in self:
            rule.field_help = CIUSRO_FIELDS.get(rule.field_key, {}).get("help", "")

    @api.depends("field_key", "xml_path", "attribute", "profile_id", "partner_id")
    def _compute_display_name(self):
        for rule in self:
            label = CIUSRO_FIELDS.get(rule.field_key, {}).get("label")
            name = label or rule.xml_path or self.env._("New rule")
            if rule.attribute:
                name = f"{name} @{rule.attribute}"
            rule.display_name = name

    @api.constrains("profile_id", "partner_id")
    def _check_owner(self):
        for rule in self:
            if bool(rule.profile_id) == bool(rule.partner_id):
                raise ValidationError(
                    self.env._(
                        "A rule belongs either to a profile or to a partner, "
                        "not to both and not to neither."
                    )
                )

    @api.constrains("scope", "xml_path", "attribute", "document_types")
    def _check_xml_path(self):
        for rule in self:
            path = rule._get_path()
            if not path:
                raise ValidationError(self.env._("The XML path is empty."))
            for doc_type, template in TEMPLATES[rule.scope].items():
                if rule.document_types not in ("all", doc_type):
                    continue
                node = template
                for tag in path:
                    node = node.get(tag) if isinstance(node, dict) else None
                    if node is None:
                        raise ValidationError(
                            self.env._(
                                "'%(path)s' is not a valid UBL path for a "
                                "%(doc_type)s: the tag '%(tag)s' does not exist "
                                "there. Writing it would make the e-Factura XML "
                                "fail to render.",
                                path=rule.xml_path,
                                doc_type=dict(DOCUMENT_TYPES).get(doc_type, doc_type),
                                tag=tag,
                            )
                        )

    @api.model_create_multi
    def create(self, vals_list):
        rules = super().create(vals_list)
        rules._check_technical_rights()
        return rules

    def write(self, vals):
        result = super().write(vals)
        if {"value_type", "field_key", "xml_path", "expression"} & set(vals):
            self._check_technical_rights()
        return result

    def _check_technical_rights(self):
        """Expressions and raw XML paths stay with the technical users.

        A field path or a fixed value cannot do more than fill a node; an
        expression runs code, and a hand written path addresses nodes the
        catalog has not vetted. Both change what is filed with ANAF, so they
        are not part of what an accountant can set on a partner.

        This is called from create/write and not from an @api.constrains:
        constraints are invoked on a sudoed recordset, where every right check
        would pass.
        """
        if self.env.su or self.env.user.has_group("base.group_system"):
            return
        for rule in self:
            if rule.value_type == "expression":
                raise ValidationError(
                    self.env._(
                        "Only the Settings group can write rules based on a Python "
                        "expression. Use a field or a fixed value instead."
                    )
                )
            if rule.field_key == CUSTOM_KEY:
                raise ValidationError(
                    self.env._(
                        "Only the Settings group can write rules on a custom XML "
                        "path. Pick a field from the list instead."
                    )
                )

    @api.constrains("value_type", "field_path", "value_fixed", "expression")
    def _check_value(self):
        required_field = {
            "field": "field_path",
            "fixed": "value_fixed",
            "expression": "expression",
        }
        for rule in self:
            field_name = required_field.get(rule.value_type)
            if field_name and not rule[field_name]:
                raise ValidationError(
                    self.env._(
                        "Rule '%(rule)s': '%(field)s' is required when the value "
                        "comes from %(value_type)s.",
                        rule=rule.display_name,
                        field=rule._fields[field_name].string,
                        value_type=dict(VALUE_TYPES)[rule.value_type],
                    )
                )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_path(self):
        self.ensure_one()
        return tuple(
            tag.strip() for tag in (self.xml_path or "").split("/") if tag.strip()
        )

    def _get_target(self):
        """Identify the node a rule writes, so a later rule can override it."""
        self.ensure_one()
        return (self.scope, self._get_path(), self.attribute or "")

    def _applies_to(self, document_type):
        self.ensure_one()
        return self.document_types in ("all", document_type)

    # ------------------------------------------------------------------
    # Value resolution
    # ------------------------------------------------------------------

    def _read_field_path(self, record):
        """Walk a dotted path on ``record``, tolerating missing fields.

        A path may cross a one2many/many2many, e.g. ``picking_ids.name``; the
        chain then ends on several values, which ``_format_value`` joins.
        """
        self.ensure_one()
        value = record
        for part in self.field_path.split("."):
            part = part.strip()
            if isinstance(value, models.Model):
                if part not in value._fields:
                    return None
                if not value:
                    return None
                value = value.mapped(part)
            elif isinstance(value, (list, tuple)):
                # The previous step already ended on plain values.
                return None
            else:
                return None
        return value

    def _format_value(self, value):
        if value is None or value is False or value == "":
            return None
        if isinstance(value, models.Model):
            if not value:
                return None
            value = [record.display_name for record in value]
        if isinstance(value, (list, tuple)):
            parts = [self._format_scalar(item) for item in value]
            value = ", ".join(part for part in parts if part)
        else:
            value = self._format_scalar(value)
        if not value:
            return None
        if self.max_len:
            value = value[: self.max_len]
        return value or None

    def _format_scalar(self, value):
        if value is None or value is False or value == "":
            return ""
        if value is True:
            return "true"
        return str(value)

    def _compute_rule_value(self, record):
        """Return the string to write for ``record``, or None to write nothing.

        ``record`` is the ``account.move`` for a document rule, the
        ``account.move.line`` for a line rule.
        """
        self.ensure_one()
        if self.value_type == "remove":
            return None
        if self.value_type == "fixed":
            value = self.value_fixed
        elif self.value_type == "field":
            value = self._read_field_path(record)
        else:
            move = record if record._name == "account.move" else record.move_id
            value = safe_eval(
                self.expression.strip(),
                {
                    "record": record,
                    "move": move,
                    "line": record if record._name == "account.move.line" else None,
                    "partner": move.commercial_partner_id,
                    "env": self.env,
                    "datetime": safe_datetime,
                },
            )
        return self._format_value(value)

    # ------------------------------------------------------------------
    # Node writing
    # ------------------------------------------------------------------

    def _walk(self, node, path, create=True):
        """Return the leaf dict of ``path`` inside the ``node`` tree.

        Odoo builds some nodes as lists (notes, payment means, party tax
        schemes); we address their first entry, creating it when needed.
        """
        for tag in path[:-1]:
            child = node.get(tag)
            if isinstance(child, list):
                if not child:
                    if not create:
                        return None
                    child.append({})
                child = child[0]
            elif not isinstance(child, dict):
                if not create:
                    return None
                child = node[tag] = {}
            node = child
        return node

    def _apply(self, node, record):
        """Write this rule's value into the ``node`` dict tree."""
        self.ensure_one()
        path = self._get_path()
        parent = self._walk(node, path, create=self.value_type != "remove")
        if parent is None:
            return
        tag = path[-1]
        key = self.attribute or "_text"

        if self.value_type == "remove":
            leaf = parent.get(tag)
            if isinstance(leaf, list):
                for entry in leaf:
                    entry.pop(key, None)
            elif isinstance(leaf, dict):
                leaf.pop(key, None)
            return

        value = self._compute_rule_value(record)
        if value is None:
            return

        leaf = parent.get(tag)
        if isinstance(leaf, list):
            if not leaf:
                leaf.append({})
            leaf = leaf[0]
        elif not isinstance(leaf, dict):
            leaf = parent[tag] = {}

        if not self.overwrite and leaf.get(key) not in (None, False, ""):
            return
        leaf[key] = value
