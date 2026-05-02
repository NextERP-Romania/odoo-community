# Copyright 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

from odoo import api, models
from odoo.tools import frozendict


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends(
        "account_id", "partner_id", "product_id", "journal_id",
    )
    def _compute_analytic_distribution(self):
        """Re-run the engine with ``journal_id`` so distribution models
        pinned to a journal can match.

        Standard's compute calls ``_get_distribution`` with 6 keys
        (``product_id``, ``product_categ_id``, ``partner_id``,
        ``partner_category_id``, ``account_prefix``, ``company_id``) —
        any model with ``journal_id`` set is excluded from the search,
        because ``_check_score`` raises ``NonMatchingDistribution``
        whenever the model has a value the caller didn't pass.

        We re-run the engine with the same payload + ``journal_id``,
        which lets journal-pinned models score (and outscore) the
        non-journal winner from super(). Lines without a journal, or
        non-product invoice lines, are left untouched.
        """
        super()._compute_analytic_distribution()
        Engine = self.env["account.analytic.distribution.model"]
        cache = {}
        for line in self:
            # Mirror the gate from standard's compute — same set of
            # lines that get the engine treatment there.
            if not (
                line.display_type == "product"
                or not line.move_id.is_invoice(include_receipts=True)
            ):
                continue
            if not line.journal_id:
                continue
            args = frozendict({
                "product_id": line.product_id.id,
                "product_categ_id": line.product_id.categ_id.id,
                "partner_id": line.partner_id.id,
                "partner_category_id": line.partner_id.category_id.ids,
                "account_prefix": line.account_id.code,
                "company_id": line.company_id.id,
                "journal_id": line.journal_id.id,
            })
            if args not in cache:
                cache[args] = Engine._get_distribution(args)
            if cache[args]:
                line.analytic_distribution = cache[args]
