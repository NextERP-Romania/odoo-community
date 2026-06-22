# Copyright 2026 NextERP Romania SRL
from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # The batch send flow (l10n_ro_edi_stock_batch) reuses these @api.model
    # entry points on stock.picking to validate / render the eTransport
    # document. The l10n_ro_edi_stock_extension overrides only enrich the
    # result when ``data["_picking_record"]`` is set (through the picking-only
    # context). Here we inject the batch as that record so the batch gets the
    # exact same stricter validation and template enrichment as a picking.

    @api.model
    def _l10n_ro_edi_stock_validate_data(self, data: dict):
        self._l10n_ro_edi_stock_inject_batch_record(data)
        return super()._l10n_ro_edi_stock_validate_data(data=data)

    @api.model
    def _l10n_ro_edi_stock_get_template_data(self, data: dict):
        self._l10n_ro_edi_stock_inject_batch_record(data)
        result = super()._l10n_ro_edi_stock_get_template_data(data=data)
        record = data.get("_picking_record")
        if record and record._name == "stock.picking.batch":
            # The base builder derives the 'PF' commercial partner code from
            # ``self.l10n_ro_edi_stock_operation_type`` which is empty when the
            # batch path calls this @api.model method on the model recordset.
            # Re-derive it here from the data dict.
            partner = data["partner_id"].commercial_partner_id
            partner_node = result["data"]["notificare"]["partenerComercial"]
            if (
                not partner_node.get("cod")
                and not partner.vat
                and data.get("l10n_ro_edi_stock_operation_type") == "30"
            ):
                partner_node["cod"] = "PF"
        return result

    @api.model
    def _l10n_ro_edi_stock_inject_batch_record(self, data):
        batch_id = self.env.context.get("l10n_ro_edi_stock_batch_id")
        if batch_id and not data.get("_picking_record"):
            data["_picking_record"] = self.env["stock.picking.batch"].browse(batch_id)
