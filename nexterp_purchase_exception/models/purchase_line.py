# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/17.0/legal/licenses/licenses.html#).

import html

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = ["purchase.order.line", "base.exception.method"]
    _name = "purchase.order.line"

    exception_ids = fields.Many2many(
        "exception.rule", string="Exceptions", copy=False, readonly=True
    )
    exceptions_summary = fields.Html(
        readonly=True,
        compute="_compute_exceptions_summary",
    )
    is_exception_danger = fields.Boolean(compute="_compute_is_exception_danger")

    @api.depends("exception_ids", "ignore_exception")
    def _compute_is_exception_danger(self):
        for rec in self:
            rec.is_exception_danger = (
                len(rec.exception_ids) > 0 and not rec.ignore_exception
            )

    @api.depends("exception_ids", "ignore_exception")
    def _compute_exceptions_summary(self):
        for rec in self:
            if rec.exception_ids and not rec.ignore_exception:
                rec.exceptions_summary = rec._get_exception_summary()
            else:
                rec.exceptions_summary = False

    def _get_exception_summary(self):
        return "<ul>{}</ul>".format(
            "".join(
                [
                    "<li>{}: <i>{}</i></li>".format(
                        *tuple(map(html.escape, (e.name, e.description)))
                    )
                    for e in self.exception_ids
                ]
            )
        )

    def _detect_exceptions(self, rule):
        res = self.env["purchase.order"]
        for rec in self:
            move_picking = super(PurchaseOrderLine, rec)._detect_exceptions(rule)
            if move_picking:
                if move_picking not in res:
                    res += move_picking
                rec.exception_ids = [(4, rule.id)]
        return res
