# Copyright (C) 2024 NextERP Romania SRL
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountEdiXmlCIUSRO(models.Model):
    _inherit = "account.edi.xml.cius_ro"

    def _get_invoice_line_item_vals(self, line, taxes_vals):
        res = super()._get_invoice_line_item_vals(line, taxes_vals)

        for customer in line.product_id.customer_ids:
            if customer.name.id == line.move_id.partner_id.id:
                res["prod_code"] = customer.product_code
            else:
                if customer.name.id == line.move_id.partner_id.parent_id.id:
                    res["prod_code"] = customer.product_code

        res["barcode"] = line.product_id.barcode
        return res

    def _get_delivery_vals_list(self, invoice):
        res = super()._get_delivery_vals_list(invoice)
        gln_module = (
            self.env["ir.module.module"]
            .sudo()
            .search(
                [("name", "=", "deltatech_gln"), ("state", "=", "installed")],
                limit=1,
            )
        )
        if gln_module:
            shipping_address = False
            if "partner_shipping_id" in invoice._fields and invoice.partner_shipping_id:
                shipping_address = invoice.partner_shipping_id
                if shipping_address == invoice.partner_id:
                    shipping_address = False
            if shipping_address:
                res = [
                    {
                        "actual_delivery_date": invoice.invoice_date,
                        "delivery_location_vals": {
                            "delivery_address_vals": self._get_partner_address_vals(
                                shipping_address
                            ),
                        },
                        "gln": shipping_address.gln,
                    }
                ]

        return res
