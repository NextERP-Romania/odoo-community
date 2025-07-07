from odoo import api, models
from odoo.tools.safe_eval import safe_eval


class AccountMoveSend(models.AbstractModel):
    _inherit = "account.move.send"

    @api.model
    def _postprocess_invoice_ubl_xml(self, invoice, invoice_data):
        # configurable embed
        if invoice.company_id.country_code == "RO":
            get_param = self.env["ir.config_parameter"].sudo().get_param
            embed_pdf = safe_eval(get_param("efactura.embed_pdf", True))
            if not embed_pdf:
                return
        else:
            return super()._postprocess_invoice_ubl_xml(invoice, invoice_data)
