# Copyright 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import models, _
from odoo.tools.misc import formatLang

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_tax_totals(self):
        super(AccountMove, self)._compute_tax_totals()

        # Add sign (-) to formatted amount and taxes in case of refund and if setting print_show_refunds is enabled
        if self.company_id.print_show_refunds and self.move_type in ['out_refund', 'in_refund']:
            for move in self:
                currency = move.currency_id or move.journal_id.currency_id or move.company_id.currency_id
                tax_totals = move.tax_totals
                if tax_totals:
                    tax_totals.update({
                        'formatted_amount_total': formatLang(self.env, (-1 * tax_totals['amount_total']), currency_obj=currency),
                        'formatted_amount_untaxed': formatLang(self.env, (-1 * tax_totals['amount_untaxed']), currency_obj=currency),
                    })

                    tax_subtotals = tax_totals['subtotals']
                    for tax_subtotal in tax_subtotals:
                        tax_subtotal.update({
                            'formatted_amount': formatLang(self.env, (-1 * tax_subtotal['amount']), currency_obj=currency),
                        })

                    groups_by_subtotal_taxes = tax_totals['groups_by_subtotal'][_("Untaxed Amount")]
                    for subtotal_tax in groups_by_subtotal_taxes:
                        subtotal_tax.update({
                            'formatted_tax_group_amount': formatLang(self.env, (-1 * subtotal_tax['tax_group_amount']), currency_obj=currency),
                            'formatted_tax_group_base_amount': formatLang(self.env, (-1 * subtotal_tax['tax_group_base_amount']), currency_obj=currency),
                        })
