# Copyright (C) 2022 Dorin Hongu <dhongu(@)gmail(.)com
# Copyright (C) 2022 NextERP Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import models


class AccountEdiXmlCIUSRO(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_ro"

    def _import_invoice_ubl_cii(self, invoice, file_data, new=False):
        res = super()._import_invoice_ubl_cii(invoice, file_data, new=new)
        invoice.date = invoice.invoice_date
        return res
