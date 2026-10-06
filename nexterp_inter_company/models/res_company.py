# Copyright (C) 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # `res.partner.is_inter_company` is stored and has nothing to depend on:
    # what makes a partner inter-company lives on `res.company`, not on the
    # partner. Without these two hooks only `_auto_init` ever sets it, so
    # every company created after the module was installed would keep an
    # unmarked partner.
    @api.model_create_multi
    def create(self, vals_list):
        companies = super().create(vals_list)
        companies.partner_id._compute_is_inter_company()
        return companies

    def write(self, vals):
        previous_partners = self.partner_id
        res = super().write(vals)
        if "partner_id" in vals:
            (previous_partners | self.partner_id)._compute_is_inter_company()
        return res

    def unlink(self):
        partners = self.partner_id
        res = super().unlink()
        partners.exists()._compute_is_inter_company()
        return res
