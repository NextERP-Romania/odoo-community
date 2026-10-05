# Copyright 2026 NextERP Romania
# License LGPL-3
"""A reusable set of CIUS-RO XML rules, shared by the partners that need it."""

import json

from odoo import api, fields, models
from odoo.exceptions import UserError

# The rule fields carried over by the JSON export/import, so a profile set up
# on one database can be replayed on another.
EXPORTED_FIELDS = (
    "sequence",
    "field_key",
    "scope",
    "xml_path",
    "attribute",
    "max_len",
    "value_type",
    "field_path",
    "value_fixed",
    "expression",
    "document_types",
    "overwrite",
    "value_required",
    "note",
)


class L10nRoEdiXmlProfile(models.Model):
    _name = "l10n_ro.edi.xml.profile"
    _description = "CIUS-RO XML profile"
    _order = "name"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        help="Leave empty to share the profile across all companies.",
    )
    rule_ids = fields.One2many(
        comodel_name="l10n_ro.edi.xml.rule",
        inverse_name="profile_id",
        string="Rules",
    )
    partner_ids = fields.One2many(
        comodel_name="res.partner",
        inverse_name="l10n_ro_edi_profile_id",
        string="Partners",
    )
    partner_count = fields.Integer(compute="_compute_partner_count")
    note = fields.Text(string="Internal notes")
    json_export = fields.Text(
        string="JSON",
        compute="_compute_json_export",
        help="The rules of this profile, ready to be pasted into the import "
        "wizard of another database.",
    )

    @api.depends("partner_ids")
    def _compute_partner_count(self):
        counts = dict(
            self.env["res.partner"]._read_group(
                [("l10n_ro_edi_profile_id", "in", self.ids)],
                groupby=["l10n_ro_edi_profile_id"],
                aggregates=["__count"],
            )
        )
        for profile in self:
            profile.partner_count = counts.get(profile, 0)

    @api.depends("rule_ids")
    def _compute_json_export(self):
        for profile in self:
            profile.json_export = json.dumps(
                profile._to_json(), indent=2, ensure_ascii=False, default=str
            )

    def _to_json(self):
        self.ensure_one()
        return {
            "name": self.name,
            "rules": [
                {
                    field: rule[field]
                    for field in EXPORTED_FIELDS
                    if rule[field] not in (False, "", 0)
                }
                for rule in self.rule_ids
            ],
        }

    def _rule_vals_from_json(self, payload):
        """Turn a JSON payload into rule values, rejecting unknown keys."""
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except ValueError as error:
                raise UserError(
                    self.env._("The pasted text is not valid JSON: %s", error)
                ) from error
        rules = payload.get("rules") if isinstance(payload, dict) else payload
        if not isinstance(rules, list):
            raise UserError(
                self.env._("Expected a list of rules, or an object with a 'rules' key.")
            )
        vals_list = []
        for rule in rules:
            if not isinstance(rule, dict):
                raise UserError(self.env._("Every rule must be a JSON object."))
            unknown = set(rule) - set(EXPORTED_FIELDS)
            if unknown:
                raise UserError(
                    self.env._(
                        "Unknown rule attributes: %s", ", ".join(sorted(unknown))
                    )
                )
            vals_list.append(dict(rule))
        return vals_list

    def action_open_partners(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Partners"),
            "res_model": "res.partner",
            "view_mode": "list,form",
            "domain": [("l10n_ro_edi_profile_id", "=", self.id)],
        }

    def action_import_json(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Import rules"),
            "res_model": "l10n_ro.edi.xml.profile.import",
            "view_mode": "form",
            "target": "new",
            "context": {"default_profile_id": self.id},
        }
