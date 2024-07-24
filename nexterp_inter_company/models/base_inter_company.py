# Copyright (C) 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class InterCompanyField(models.AbstractModel):
    _name = "base.inter.company"
    _description = """
        Inter Company Mixin model for checking if a record is
        inter company transaction or not."""

    is_inter_company = fields.Boolean(
        compute="_compute_is_inter_company",
        readonly=False,
        store=True,
        index=True,
        help="The field computes if the record represent a "
        "inter company transaction or not.",
    )

    def _check_company_id_in_fields(self):
        has_company = "company_id" in self.env[self._name]._fields
        if has_company:
            return ["company_id"]
        return []

    @api.depends(lambda self: self._check_partner_id_in_fields())
    @api.depends_context("company")
    def _compute_is_inter_company(self):
        all_companies = self.sudo().env["res.company"].search([])
        for record in self:
            has_company = record._check_company_id_in_fields()
            has_company = has_company and record.company_id
            company = record.company_id if has_company else record.env.company

            record_companies = all_companies - company
            record_companies_partners = [
                comp.partner_id.id for comp in record_companies
            ]
            record_companies_vats = [comp.partner_id.vat for comp in record_companies]

            is_inter_company = False
            if "commercial_partner_id" in self._fields:
                if record.commercial_partner_id.id in record_companies_partners:
                    is_inter_company = True
                elif (
                    record.commercial_partner_id.vat
                    and record.commercial_partner_id.vat in record_companies_vats
                ):
                    is_inter_company = True
            elif "partner_id" in self._fields:
                if record.partner_id.id in record_companies_partners:
                    is_inter_company = True
                elif (
                    record.partner_id.vat
                    and record.partner_id.vat in record_companies_vats
                ):
                    is_inter_company = True
            else:
                _logger.warning(
                    f"""On model {self._name} you do not have field
                    commercial_partner_id or partner_id; but you inherited
                    inter company mixin. Please add one of the fields to the
                    model to use inter company or update the compute method
                    with the right partner field."""
                )
            record.is_inter_company = is_inter_company

    def _check_partner_id_in_fields(self):
        has_commercial_partner = "commercial_partner_id" in self.env[self._name]._fields
        if has_commercial_partner:
            return ["commercial_partner_id"]
        has_partner = "partner_id" in self.env[self._name]._fields
        if has_partner:
            return ["partner_id"]
        return []
