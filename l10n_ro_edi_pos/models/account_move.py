# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    l10n_ro_fiscal_receipt_number = fields.Char(
        string="Fiscal Receipt Number",
        compute="_compute_l10n_ro_fiscal_receipt_number",
        store=True,
        readonly=False,
        copy=False,
        help="The fiscal receipt this invoice was issued for. Filled from the "
        "point of sale orders behind the invoice; set by hand for an invoice "
        "issued later, in the back office, for a sale already on a receipt. "
        "Such an invoice goes to e-Factura with type code 751: the sale and "
        "its VAT were declared with the receipt.",
    )

    @api.depends("pos_order_ids.l10n_ro_fiscal_receipt_number")
    def _compute_l10n_ro_fiscal_receipt_number(self):
        for move in self:
            numbers = move.pos_order_ids.filtered(
                "l10n_ro_fiscal_receipt_number"
            ).mapped("l10n_ro_fiscal_receipt_number")
            if numbers:
                move.l10n_ro_fiscal_receipt_number = ", ".join(numbers)
            elif not move.l10n_ro_fiscal_receipt_number:
                move.l10n_ro_fiscal_receipt_number = False

    def write(self, vals):
        # The number decides the e-Factura type code (751): once the invoice
        # is posted or in the SPV it is fixed. The recompute from the point of
        # sale orders does not go through ``write`` and stays allowed.
        if "l10n_ro_fiscal_receipt_number" in vals:
            new = vals["l10n_ro_fiscal_receipt_number"] or False
            for move in self:
                if (move.l10n_ro_fiscal_receipt_number or False) != new and (
                    move.state != "draft"
                    or move.l10n_ro_edi_state in ("invoice_sent", "invoice_validated")
                ):
                    raise UserError(
                        self.env._(
                            "The fiscal receipt number of %(name)s can only be"
                            " changed while the invoice is a draft not sent to"
                            " the SPV.",
                            name=move.display_name,
                        )
                    )
        return super().write(vals)
