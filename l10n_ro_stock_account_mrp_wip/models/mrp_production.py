# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from datetime import datetime, time

from odoo import Command, api, fields, models


class MrpProduction(models.Model):
    _name = "mrp.production"
    _inherit = ["mrp.production", "l10n.ro.mixin"]

    l10n_ro_auto_wip_accounting = fields.Boolean(
        string="Auto WIP Accounting",
        compute="_compute_l10n_ro_auto_wip_accounting",
        store=True,
        readonly=False,
        help="If checked, the WIP accounts will be automatically handled "
        "during manufacturing operations.",
    )

    company_currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Company Currency",
        readonly=True,
    )
    l10n_ro_wip_initial = fields.Monetary(
        string="WIP Initial",
        currency_field="company_currency_id",
        help="The initial WIP amount for this manufacturing order.",
    )
    l10n_ro_wip = fields.Monetary(
        string="WIP",
        compute="_compute_l10n_ro_wip",
        currency_field="company_currency_id",
        store=True,
        help="The current WIP amount for this manufacturing order.",
    )
    l10n_ro_wip_total = fields.Monetary(
        string="WIP Total",
        compute="_compute_l10n_ro_wip",
        currency_field="company_currency_id",
        store=True,
        help="The total WIP amount for this manufacturing order.",
    )
    # Native ``wip_move_ids`` (mrp_account) holds the account moves linked to
    # this MO through ``account.move.wip_production_ids``. We reuse it instead
    # of a private one2many.
    l10n_ro_wip_account_move_count = fields.Integer(
        string="WIP Account Moves", compute="_compute_l10n_ro_wip_account_move_count"
    )

    @api.depends("bom_id.l10n_ro_auto_wip_accounting")
    def _compute_l10n_ro_auto_wip_accounting(self):
        for production in self:
            production.l10n_ro_auto_wip_accounting = (
                production.bom_id.l10n_ro_auto_wip_accounting
            )

    def _get_l10n_ro_wip_account(self):
        self.ensure_one()
        accounts = (
            self.product_id.product_tmpl_id.with_company(self.company_id)
            .sudo()
            .get_product_accounts()
        )
        return accounts.get("production_wip")

    @api.depends(
        "l10n_ro_wip_initial",
        "wip_move_ids",
        "wip_move_ids.line_ids.balance",
        "wip_move_ids.state",
    )
    def _compute_l10n_ro_wip(self):
        for production in self:
            wip_account = production._get_l10n_ro_wip_account()
            wip_amount = 0.0
            if wip_account:
                lines = production.wip_move_ids.sudo().line_ids.filtered(
                    lambda line, acc=wip_account: line.account_id == acc
                    and line.parent_state == "posted"
                )
                wip_amount = sum(lines.mapped("balance"))
            production.l10n_ro_wip = wip_amount
            production.l10n_ro_wip_total = production.l10n_ro_wip_initial + wip_amount

    @api.depends("wip_move_ids")
    def _compute_l10n_ro_wip_account_move_count(self):
        for production in self:
            production.l10n_ro_wip_account_move_count = len(
                production.wip_move_ids.sudo()
            )

    def action_view_wip_account_moves(self):
        """Display the WIP account moves related to this manufacturing order."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_journal_line"
        )
        if len(self.wip_move_ids) > 1:
            action["domain"] = [("id", "in", self.wip_move_ids.ids)]
        elif self.wip_move_ids:
            action["res_id"] = self.wip_move_ids.id
            move_form = self.env.ref("account.view_move_form", False)
            move_form_view = [(move_form and move_form.id or False, "form")]
            action["views"] = move_form_view + [
                (state, view)
                for state, view in action.get("views", [])
                if view != "form"
            ]
        action["context"] = dict(self._context, default_origin=self.name)
        return action

    def _cal_price(self, consumed_moves):
        if self.l10n_ro_auto_wip_accounting:
            # For WIP accounting the finished cost must be computed from all
            # the raw material actually consumed during the whole production,
            # not only from the moves validated at production registration.
            consumed_moves = self.move_raw_ids.filtered(lambda x: x.state == "done")
        return super()._cal_price(consumed_moves)

    def button_mark_done(self):
        res = super().button_mark_done()
        # Order finished: clear its work in progress (331 -> 0). The finished
        # goods note (345 = 711) already stands on its own.
        self.filtered(lambda mo: mo.state == "done")._l10n_ro_update_wip(target=0.0)
        return res

    def _l10n_ro_update_wip(self, target=None):
        """Bring the WIP account (331) to the current work-in-progress value by
        posting only the incremental difference (Dr 331 / Cr 711, or the
        reverse), reusing the standard Odoo WIP wizard computation.

        Called automatically on component consumption, work order finish and
        time logged on a not-done work order; called with ``target=0`` when the
        order is done, to clear its WIP.
        """
        for production in self.filtered("l10n_ro_auto_wip_accounting"):
            production._l10n_ro_post_wip_delta(target=target)

    def _l10n_ro_post_wip_delta(self, target=None):
        self.ensure_one()
        company = self.company_id
        currency = company.currency_id
        date = fields.Date.context_today(self)
        wizard = self.env["mrp.account.wip.accounting"].with_company(company).new({})
        lines = wizard._get_line_vals(self, datetime.combine(date, time.max))
        debit_vals = next((cmd[2] for cmd in lines if cmd[2].get("debit")), None)
        credit_vals = next((cmd[2] for cmd in lines if cmd[2].get("credit")), None)
        if not debit_vals or not credit_vals:
            return self.env["account.move"]
        wip_account_id = debit_vals["account_id"]  # 331
        counterpart_id = credit_vals["account_id"]  # 711
        if target is None:
            target = debit_vals["debit"]  # component value + overhead
        # Recompute the already-posted WIP before measuring the delta.
        self.invalidate_recordset(["l10n_ro_wip"])
        delta = currency.round(target - self.l10n_ro_wip)
        if currency.is_zero(delta):
            return self.env["account.move"]

        accounts = self.product_id.product_tmpl_id.with_company(
            company
        ).get_product_accounts()
        journal = accounts.get("stock_journal") or company.account_stock_journal_id
        debit_acc, credit_acc = (
            (wip_account_id, counterpart_id)
            if delta > 0
            else (counterpart_id, wip_account_id)
        )
        amount = abs(delta)
        label = self.env._("WIP - %(name)s", name=self.name)
        move = (
            self.env["account.move"]
            .sudo()
            .create(
                {
                    "journal_id": journal.id,
                    "date": date,
                    "move_type": "entry",
                    "ref": label,
                    "company_id": company.id,
                    "wip_production_ids": [Command.link(self.id)],
                    "line_ids": [
                        Command.create(
                            {
                                "name": label,
                                "account_id": debit_acc,
                                "debit": amount,
                                "credit": 0.0,
                            }
                        ),
                        Command.create(
                            {
                                "name": label,
                                "account_id": credit_acc,
                                "debit": 0.0,
                                "credit": amount,
                            }
                        ),
                    ],
                }
            )
        )
        move._post()
        return move
