# Copyright (C) 2022 Dorin Hongu <dhongu(@)gmail(.)com
# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    peppol_eas = fields.Selection(
        selection_add=[
            ("AN", "AN - O.F.T.P. (ODETTE File Transfer Protocol)"),
            ("AQ", "AQ - X.400 address for mail text"),
            ("AS", "AS - AS2 exchange"),
            ("AU", "AU - File Transfer Protocol"),
            ("EM", "EM - Electronic mail"),
        ],
    )
    l10n_ro_edi_ubl_no_send = fields.Boolean(
        "Romania - No send UBL",
        help="Check this if the partner should not receive UBL invoices.",
    )
    l10n_ro_edi_ubl_no_send_cnp = fields.Boolean(
        "Romania - No send CNP UBL",
        help="Check this if the partner should not receive UBL invoices on their CNP.",
    )

    def _retrieve_partner(
        self, name=None, phone=None, mail=None, vat=None, domain=None, company=None
    ):
        if self.env.company.country_id == self.env.ref("base.ro"):
            phone = False
            mail = False
            name = False
        return super()._retrieve_partner(
            name=name, phone=phone, mail=mail, vat=vat, domain=domain, company=company
        )
