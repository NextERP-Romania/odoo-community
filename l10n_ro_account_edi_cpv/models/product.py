# Copyright (C) 2025 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    l10n_ro_cpv_code = fields.Many2one(
        "l10n.ro.cpv.code",
        string="Romania - CPV Code",
        compute="_compute_l10n_ro_cpv_code",
        inverse="_inverse_l10n_ro_cpv_code",
        store=True,
    )

    @api.depends("product_variant_ids", "product_variant_ids.l10n_ro_cpv_code")
    def _compute_l10n_ro_cpv_code(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1
        )
        for template in unique_variants:
            template.l10n_ro_cpv_code = template.product_variant_ids.l10n_ro_cpv_code
        for template in self - unique_variants:
            template.l10n_ro_cpv_code = False

    def _inverse_l10n_ro_cpv_code(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.l10n_ro_cpv_code = (
                    template.l10n_ro_cpv_code
                )


class ProductProduct(models.Model):
    _inherit = "product.product"

    l10n_ro_cpv_code = fields.Many2one("l10n.ro.cpv.code", string="Romania - CPV Code")
