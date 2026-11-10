# Copyright 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

import copy

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _nexterp_report_tax_totals(self):
        """Tax totals as printed on the invoice report.

        With the ``print_show_refunds`` setting, credit notes print their
        totals negative. The sign is flipped on a copy only: ``tax_totals`` is
        a computed field with an inverse (it drives the form widget and can
        write back on the move), so it must keep Odoo's own values.
        """
        self.ensure_one()
        # l10n_ro_edi_extension_storno prints its storno invoices negative
        # already: take its copy as is, never negate it a second time.
        if hasattr(self, "_l10n_ro_is_storno_report") and (
            self._l10n_ro_is_storno_report()
        ):
            return self._l10n_ro_report_tax_totals()
        tax_totals = self.tax_totals
        if not (
            tax_totals
            and self.company_id.print_show_refunds
            and self.move_type in ("out_refund", "in_refund")
        ):
            return tax_totals
        tax_totals = copy.deepcopy(tax_totals)
        for key in [
            "base_amount",
            "base_amount_currency",
            "tax_amount",
            "tax_amount_currency",
            "total_amount",
            "total_amount_currency",
        ]:
            if key in tax_totals:
                tax_totals[key] = -1 * tax_totals[key]
        for subtotal in tax_totals.get("subtotals", []):
            for key in [
                "base_amount",
                "base_amount_currency",
                "tax_amount",
                "tax_amount_currency",
            ]:
                if key in subtotal:
                    subtotal[key] = -1 * subtotal[key]
            for group in subtotal.get("tax_groups", []):
                for key in [
                    "base_amount",
                    "base_amount_currency",
                    "display_base_amount",
                    "display_base_amount_currency",
                    "tax_amount",
                    "tax_amount_currency",
                ]:
                    if key in group:
                        group[key] = -1 * group[key]
        return tax_totals


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def get_section_subtotal(self):
        res = super().get_section_subtotal()
        sign = (
            self.company_id.print_show_refunds
            and self.move_type
            in [
                "out_refund",
                "in_refund",
            ]
            and -1
            or 1
        )
        return sign * res

    def get_section_tax_amount(self):
        section_lines = self._get_section_lines()
        sign = (
            self.company_id.print_show_refunds
            and self.move_type
            in [
                "out_refund",
                "in_refund",
            ]
            and -1
            or 1
        )
        section_tax_amount = sign * sum(
            line.price_total - line.price_subtotal for line in section_lines
        )
        return section_tax_amount

    def get_section_total_amount(self):
        section_lines = self._get_section_lines()
        sign = (
            self.company_id.print_show_refunds
            and self.move_type
            in [
                "out_refund",
                "in_refund",
            ]
            and -1
            or 1
        )
        return sign * sum(section_lines.mapped("price_total"))

    def _get_child_lines(self):
        res = super()._get_child_lines()
        sign = (
            self.company_id.print_show_refunds
            and self.move_id.move_type in ["out_refund", "in_refund"]
            and -1
            or 1
        )
        for line in res:
            price = line["price_subtotal"] / line["quantity"] if line["quantity"] else 0
            line["price_unit"] = price
            line["price_total"] = sign * line.get("price_total", 0)
            line["price_subtotal"] = sign * line.get("price_subtotal", 0)
            line["quantity"] = sign * line.get("quantity", 0)
            line["tax_amount"] = line.get("price_total", 0) - line.get(
                "price_subtotal", 0
            )
        return res
