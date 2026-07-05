# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

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

    def action_view_move_wip(self):
        action = super().action_view_move_wip()
        # The native action registers only the list view, so a WIP journal entry
        # cannot be opened in form from the list. Add the account move form view.
        if action.get("res_model") == "account.move" and not any(
            view[1] == "form" for view in action.get("views", [])
        ):
            form = self.env.ref("account.view_move_form", False)
            action["views"] = list(action.get("views", [])) + [
                (form.id if form else False, "form")
            ]
            action.setdefault("view_mode", "list,form")
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
        for production in self.filtered(
            lambda mo: mo.state == "done" and mo.l10n_ro_auto_wip_accounting
        ):
            production.invalidate_recordset(["l10n_ro_wip"])
            if not production.company_id.currency_id.is_zero(production.l10n_ro_wip):
                production._l10n_ro_post_wip_entry(
                    -production.l10n_ro_wip,
                    product=production.product_id,
                    label=production.env._(
                        "WIP clearing - %(name)s", name=production.name
                    ),
                )
        return res

    def _l10n_ro_wip_accounts(self):
        """Return (journal, wip account 331, counterpart 711) for this order,
        taken from the finished product / category."""
        self.ensure_one()
        accounts = self.product_id.product_tmpl_id.with_company(
            self.company_id
        ).get_product_accounts()
        wip_account = accounts.get("production_wip")
        counterpart = accounts.get("production_wip_overhead") or accounts.get("expense")
        journal = accounts.get("stock_journal") or (
            self.company_id.account_stock_journal_id
        )
        return journal, wip_account, counterpart

    def _l10n_ro_post_wip_entry(self, value, product=None, label=None, workorder=None):
        """Post one WIP entry (Dr 331 / Cr 711 for a positive value, reversed
        for a negative one), keeping the product on both lines so the entry is
        traceable to the consumed component or the finished product.

        One entry is posted per stock move / work order, not aggregated.
        """
        self.ensure_one()
        currency = self.company_id.currency_id
        value = currency.round(value)
        if currency.is_zero(value):
            return self.env["account.move"]
        journal, wip_account, counterpart = self._l10n_ro_wip_accounts()
        if not journal or not wip_account or not counterpart:
            return self.env["account.move"]
        label = label or self.env._("WIP - %(name)s", name=self.name)
        debit_acc, credit_acc = (
            (wip_account, counterpart) if value > 0 else (counterpart, wip_account)
        )
        amount = abs(value)
        line = {"name": label}
        if product:
            line["product_id"] = product.id
        move = (
            self.env["account.move"]
            .sudo()
            .create(
                {
                    "journal_id": journal.id,
                    "date": fields.Date.context_today(self),
                    "move_type": "entry",
                    "ref": label,
                    "company_id": self.company_id.id,
                    "l10n_ro_wip_workorder_id": workorder.id if workorder else False,
                    "wip_production_ids": [Command.link(self.id)],
                    "line_ids": [
                        Command.create(
                            {
                                **line,
                                "account_id": debit_acc.id,
                                "debit": amount,
                                "credit": 0.0,
                            }
                        ),
                        Command.create(
                            {
                                **line,
                                "account_id": credit_acc.id,
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
