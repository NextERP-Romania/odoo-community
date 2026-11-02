# Copyright (C) 2026 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import copy

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _l10n_ro_is_storno_report(self):
        """Customer credit note printed as a storno invoice (negative values)."""
        self.ensure_one()
        return (
            self.move_type == "out_refund"
            and self.company_id.l10n_ro_credit_note_einvoice
        )

    def _l10n_ro_report_quantity_signed(self):
        """The quantity is already printed negative by
        ``nexterp_account_invoice_report`` (refunds shown with sign)."""
        self.ensure_one()
        company = self.company_id
        return bool(
            "print_show_refunds" in company._fields
            and company.print_show_refunds
            and company.print_invoice_tax_value
        )

    def _l10n_ro_storno_negate(self, values):
        """Copy of ``values`` with every numeric ``*amount*``, ``quantity``,
        ``price_subtotal`` and ``price_total`` negated, walking nested dicts
        and lists. Prices and percentages are left as they are."""

        def _is_negated_key(key):
            return "amount" in key or key in (
                "quantity",
                "price_subtotal",
                "price_total",
            )

        def _walk(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if (
                        isinstance(key, str)
                        and _is_negated_key(key)
                        and isinstance(item, int | float)
                        and not isinstance(item, bool)
                    ):
                        value[key] = -item if item else item
                    else:
                        _walk(item)
            elif isinstance(value, list):
                for item in value:
                    _walk(item)
            return value

        return _walk(copy.deepcopy(values))

    def _l10n_ro_report_tax_totals(self):
        self.ensure_one()
        if self.tax_totals and self._l10n_ro_is_storno_report():
            return self._l10n_ro_storno_negate(self.tax_totals)
        return self.tax_totals
