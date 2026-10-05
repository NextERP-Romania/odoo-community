# Copyright 2026 NextERP Romania
# License LGPL-3
"""Replay a profile exported as JSON from another database."""

from odoo import fields, models


class L10nRoEdiXmlProfileImport(models.TransientModel):
    _name = "l10n_ro.edi.xml.profile.import"
    _description = "Import CIUS-RO XML rules"

    profile_id = fields.Many2one(
        comodel_name="l10n_ro.edi.xml.profile",
        string="Profile",
        required=True,
        ondelete="cascade",
    )
    json_text = fields.Text(
        string="JSON",
        required=True,
        help="Paste here the JSON shown on the source profile.",
    )
    mode = fields.Selection(
        selection=[
            ("add", "Add to the existing rules"),
            ("replace", "Replace the existing rules"),
        ],
        required=True,
        default="add",
    )

    def action_import(self):
        self.ensure_one()
        vals_list = self.profile_id._rule_vals_from_json(self.json_text)
        if self.mode == "replace":
            self.profile_id.rule_ids.unlink()
        self.env["l10n_ro.edi.xml.rule"].create(
            [dict(vals, profile_id=self.profile_id.id) for vals in vals_list]
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "message": self.env._("%s rules imported.", len(vals_list)),
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
