# Copyright 2026 NextERP Romania
# License LGPL-3
"""Where a partner's CIUS-RO XML rules are configured and resolved."""

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_ro_edi_profile_id = fields.Many2one(
        comodel_name="l10n_ro.edi.xml.profile",
        string="e-Factura XML profile",
        help="Set of XML rules shared with the other partners that have the "
        "same e-invoicing requirements.",
    )
    l10n_ro_edi_xml_rule_ids = fields.One2many(
        comodel_name="l10n_ro.edi.xml.rule",
        inverse_name="partner_id",
        string="Specific XML rules",
        help="Rules that apply to this partner only. They override the rules "
        "of the profile that write the same node.",
    )

    def _l10n_ro_edi_get_xml_rules(self, scope, document_type):
        """Return the rules to apply for this partner, most specific last.

        A contact inherits the rules of its commercial partner and may refine
        them: when two rules write the same node, the last one wins, so a rule
        set on the contact beats one of the commercial partner, and a rule set
        on a partner beats one of its profile.
        """
        self.ensure_one()
        partners = self.commercial_partner_id
        if self != self.commercial_partner_id:
            partners |= self

        by_target = {}
        for partner in partners:
            rules = partner.l10n_ro_edi_profile_id.rule_ids.sorted(
                lambda rule: (rule.sequence, rule.id)
            )
            rules += partner.l10n_ro_edi_xml_rule_ids.sorted(
                lambda rule: (rule.sequence, rule.id)
            )
            for rule in rules:
                if rule.scope != scope or not rule._applies_to(document_type):
                    continue
                by_target[rule._get_target()] = rule

        return list(by_target.values())
