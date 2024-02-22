# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

import html

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = ["stock.picking", "base.exception"]
    _name = "stock.picking"

    def button_validate(self):
        if self.detect_exceptions() and not self.ignore_exception:
            return self._popup_exceptions()
        return super().button_validate()


class StockMove(models.Model):
    _inherit = ["stock.move", "base.exception.method"]
    _name = "stock.move"

    exception_ids = fields.Many2many(
        "exception.rule", string="Exceptions", copy=False, readonly=True
    )
    exceptions_summary = fields.Html(
        readonly=True, compute="_compute_exceptions_summary"
    )

    @api.depends("exception_ids", "ignore_exception")
    def _compute_exceptions_summary(self):
        for rec in self:
            if rec.exception_ids and not rec.ignore_exception:
                rec.exceptions_summary = rec._get_exception_summary()
            else:
                rec.exceptions_summary = False

    def _get_exception_summary(self):
        return "<ul>%s</ul>" % "".join(
            [
                "<li>%s: <i>%s</i></li>"
                % tuple(map(html.escape, (e.name, e.description)))
                for e in self.exception_ids
            ]
        )

    def _detect_exceptions(self, rule):
        res = self.env["stock.picking"]
        for rec in self:
            move_picking = super(StockMove, rec)._detect_exceptions(rule)
            if move_picking:
                if move_picking not in res:
                    res += move_picking
                rec.exception_ids = [(4, rule.id)]
        return res
