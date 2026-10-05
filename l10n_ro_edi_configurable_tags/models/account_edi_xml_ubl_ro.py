# Copyright 2026 NextERP Romania
# License LGPL-3
"""Apply the partner's XML rules to the generated CIUS-RO document.

CIUS-RO still builds its XML through the ``ubl_20`` skeleton
(``_get_invoice_node``), which ends each document and each line with the same
extension points Odoo uses for its Peppol optional fields. Hooking there means
the rules see a finished node tree and can either complete it or correct what
Odoo computed, without reordering anything: ``dict_to_xml`` takes the tag order
from the UBL template, not from the order keys were inserted.
"""

from odoo import models


class AccountEdiXmlUblRo(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_ro"

    def _add_invoice_optional_nodes(self, document_node, vals):
        # EXTENDS 'account.edi.xml.ubl_20'
        result = super()._add_invoice_optional_nodes(document_node, vals)
        invoice = vals["invoice"]
        rules = invoice.commercial_partner_id._l10n_ro_edi_get_xml_rules(
            "document", vals["document_type"]
        )
        for rule in rules:
            rule._apply(document_node, invoice)
        return result

    def _add_invoice_line_optional_nodes(self, line_node, vals):
        # EXTENDS 'account.edi.xml.ubl_20'
        result = super()._add_invoice_line_optional_nodes(line_node, vals)
        record = vals["base_line"]["record"]
        if not isinstance(record, models.Model) or record._name != "account.move.line":
            return result
        rules = vals["invoice"].commercial_partner_id._l10n_ro_edi_get_xml_rules(
            "line", vals["document_type"]
        )
        for rule in rules:
            rule._apply(line_node, record)
        return result

    def _export_invoice_constraints(self, invoice, vals):
        # EXTENDS 'account.edi.xml.ubl_ro'
        constraints = super()._export_invoice_constraints(invoice, vals)
        partner = invoice.commercial_partner_id
        document_type = vals["document_type"]

        for rule in partner._l10n_ro_edi_get_xml_rules("document", document_type):
            if rule.value_required and rule._compute_rule_value(invoice) is None:
                constraints[f"l10n_ro_edi_rule_{rule.id}"] = self.env._(
                    "The e-Factura rule '%(rule)s' of partner %(partner)s "
                    "produced no value for this invoice.",
                    rule=rule.display_name,
                    partner=partner.display_name,
                )

        line_rules = partner._l10n_ro_edi_get_xml_rules("line", document_type)
        if line_rules:
            lines = invoice.invoice_line_ids.filtered(
                lambda line: line.display_type == "product"
            )
            for rule in line_rules:
                if not rule.value_required:
                    continue
                missing = lines.filtered(
                    lambda line, rule=rule: rule._compute_rule_value(line) is None
                )
                if missing:
                    constraints[f"l10n_ro_edi_rule_{rule.id}"] = self.env._(
                        "The e-Factura rule '%(rule)s' of partner %(partner)s "
                        "produced no value on the lines: %(lines)s.",
                        rule=rule.display_name,
                        partner=partner.display_name,
                        lines=", ".join(filter(None, missing.mapped("name"))),
                    )

        return constraints
