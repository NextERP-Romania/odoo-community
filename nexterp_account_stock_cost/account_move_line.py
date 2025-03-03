# Copyright 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/15.0/legal/licenses/licenses.html#).

from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    stock_cost = fields.Float(
        compute="_compute_stock_cost",
        store=True,
        index=1
    )
    stock_cost_product = fields.Float(
        compute="_compute_stock_cost",
        store=True,
        index=1
    )
    stock_cost_price_diff = fields.Float(
        compute="_compute_stock_cost",
        store=True,
        index=1
    )
    stock_cost_additional_cost = fields.Float(
        compute="_compute_stock_cost",
        store=True,
        index=1
    )
    stock_cost_supplier_id = fields.Many2one(
        comodel_name='res.partner',
        ondelete='restrict',
        compute="_compute_stock_cost",
        store=True,
        index=1
    )

    @api.depends('sale_line_ids', 'purchase_line_id', 'sale_line_ids.move_ids.stock_valuation_layer_ids', 'purchase_line_id.move_ids.stock_valuation_layer_ids')
    def _compute_stock_cost(self):
        for move_line in self:
            reception = False
            stock_cost = 0
            stock_cost_price_diff = 0
            stock_cost_additional_cost = 0
            stock_cost_supplier_id = self.env['res.partner']
            svls = self.env['stock.valuation.layer'].search([('l10n_ro_invoice_line_id', '=', move_line.id)])
            if not svls:
                stock_moves = move_line.sale_line_ids.move_ids + move_line.purchase_line_id.move_ids
                svls = stock_moves.mapped('stock_valuation_layer_ids')
            for svl in svls:
                no_track = False
                sign = -1 if svl.l10n_ro_valued_type in ("delivery_return","reception") else 1
                stock_cost += -1 * svl.value * sign
                svl_tracks = svl.l10n_ro_svl_track_src_ids
                if svl.l10n_ro_valued_type == "reception":
                    reception = True
                    no_track = True
                    stock_valuation_layer_id = self.env['stock.valuation.layer'].search([('stock_valuation_layer_id', '=', svl.id)])
                    svl_tracks = svl + stock_valuation_layer_id
                if svl.l10n_ro_valued_type == "delivery_return":
                    svl_tracks = svl.l10n_ro_svl_track_src_ids.svl_src_id.mapped('l10n_ro_svl_track_src_ids')

                for svl_track in svl_tracks:
                    # cost of the product (only product has value for quantity)
                    # price_diff and additional_cost will always have value 0 for quantity
                    if no_track == True:
                        if svl_track.l10n_ro_valued_type == "reception":
                            svl_source = svl_track
                    else:
                        svl_source = svl_track.svl_src_id
                    if svl_track.quantity:
                        # get the supplier
                        if not stock_cost_supplier_id and svl_source.stock_move_id.picking_id.partner_id:
                            stock_cost_supplier_id = svl_source.stock_move_id.picking_id.partner_id
                    if svl_source.stock_landed_cost_id:
                        svl_quantity = (svl_source.quantity or svl_source.stock_valuation_layer_id.quantity)
                        percentage = -sign * svl.quantity / svl_quantity
                        if "l10n_ro_cost_type" in self.env["stock.landed.cost"]._fields:
                            if svl_source.stock_landed_cost_id.l10n_ro_cost_type == "price_diff":
                                stock_cost_price_diff += (sign * svl_source.value * percentage)
                            else:
                                stock_cost_additional_cost += (sign * svl_source.value * percentage)
                        else:
                            stock_cost_additional_cost += (sign * svl_source.value * percentage)
                if svl.stock_landed_cost_id:
                    if "l10n_ro_cost_type" in self.env["stock.landed.cost"]._fields:
                        if svl.stock_landed_cost_id.l10n_ro_cost_type == "price_diff":
                            stock_cost_price_diff += (-sign * svl.value)
                        else:
                            stock_cost_additional_cost += (-sign * svl.value)
                    else:
                        stock_cost_additional_cost += (-sign * svl.value)

            move_line.stock_cost = stock_cost
            move_line.stock_cost_product = stock_cost - stock_cost_price_diff - stock_cost_additional_cost
            move_line.stock_cost_price_diff = stock_cost_price_diff
            move_line.stock_cost_additional_cost = stock_cost_additional_cost if not reception else  -stock_cost_additional_cost
            move_line.stock_cost_supplier_id = stock_cost_supplier_id
