# Copyright 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import _, fields, models
from odoo.exceptions import AccessError


class PosSession(models.Model):
    _inherit = "pos.session"

    def _compute_cash_balance(self):
        if not self.company_id.pos_session_close_by_date:
            return super(PosSession, self)._compute_cash_balance()
        else:
            for session in self:
                cash_payment_method = session.payment_method_ids.filtered(
                    "is_cash_count"
                )[:1]
                if cash_payment_method:
                    total_cash_payment = 0.0
                    last_session = session.search(
                        [
                            ("config_id", "=", session.config_id.id),
                            ("start_at", "<", session.start_at),
                        ],
                        limit=1,
                    )
                    result = self.env["pos.payment"]._read_group(
                        [
                            ("session_id", "=", session.id),
                            ("payment_method_id", "=", cash_payment_method.id),
                        ],
                        ["amount"],
                        ["session_id"],
                    )
                    if result:
                        total_cash_payment = result[0]["amount"]

                    if session.state == "closed":
                        session.cash_register_total_entry_encoding = (
                            session.cash_real_transaction + total_cash_payment
                        )
                    else:
                        session.cash_register_total_entry_encoding = (
                            sum(session.statement_line_ids.mapped("amount"))
                            + total_cash_payment
                        )

                    session.cash_register_balance_end = (
                        last_session.cash_register_balance_end_real
                        + session.cash_register_total_entry_encoding
                    )
                    session.cash_register_difference = (
                        session.cash_register_balance_end_real
                        - session.cash_register_balance_end
                    )
                else:
                    session.cash_register_total_entry_encoding = 0.0
                    session.cash_register_balance_end = 0.0
                    session.cash_register_difference = 0.0

    def action_pos_session_open(self):
        if not self.company_id.pos_session_close_by_date:
            return super(PosSession, self).action_pos_session_open()
        else:
            # we only open sessions that haven't already been opened
            for session in self.filtered(
                lambda session: session.state == "opening_control"
            ):
                values = {}
                if not session.start_at:
                    values["start_at"] = fields.Datetime.now()
                if session.config_id.cash_control and not session.rescue:
                    last_session = self.search(
                        [
                            ("config_id", "=", session.config_id.id),
                            ("start_at", "<", session.start_at),
                        ],
                        limit=1,
                    )
                    session.cash_register_balance_start = (
                        last_session.cash_register_balance_end_real
                    )  # defaults to 0 if lastsession is empty
                else:
                    values["state"] = "opened"
                session.write(values)
            return True

    def get_closing_control_data(self):
        if not self.company_id.pos_session_close_by_date:
            return super(PosSession, self).get_closing_control_data()
        else:
            if not self.env.user.has_group("point_of_sale.group_pos_user"):
                raise AccessError(
                    _(
                        "You don't have the access rights to get the \
                        point of sale closing control data"
                    )
                )
            self.ensure_one()
            orders = self.order_ids.filtered(
                lambda o: o.state == "paid" or o.state == "invoiced"
            )
            payments = orders.payment_ids.filtered(
                lambda p: p.payment_method_id.type != "pay_later"
            )
            pay_later_payments = orders.payment_ids - payments
            cash_payment_method_ids = self.payment_method_ids.filtered(
                lambda pm: pm.type == "cash"
            )
            default_cash_payment_method_id = (
                cash_payment_method_ids[0] if cash_payment_method_ids else None
            )
            total_default_cash_payment_amount = (
                sum(
                    payments.filtered(
                        lambda p: p.payment_method_id == default_cash_payment_method_id
                    ).mapped("amount")
                )
                if default_cash_payment_method_id
                else 0
            )
            other_payment_method_ids = (
                self.payment_method_ids - default_cash_payment_method_id
                if default_cash_payment_method_id
                else self.payment_method_ids
            )
            cash_in_count = 0
            cash_out_count = 0
            cash_in_out_list = []
            last_session = self.search(
                [
                    ("config_id", "=", self.config_id.id),
                    ("start_at", "<", self.start_at),
                ],
                limit=1,
            )
            for cash_move in self.sudo().statement_line_ids.sorted("create_date"):
                if cash_move.amount > 0:
                    cash_in_count += 1
                    name = f"Cash in {cash_in_count}"
                else:
                    cash_out_count += 1
                    name = f"Cash out {cash_out_count}"
                cash_in_out_list.append(
                    {
                        "name": cash_move.payment_ref
                        if cash_move.payment_ref
                        else name,
                        "amount": cash_move.amount,
                    }
                )

            return {
                "orders_details": {
                    "quantity": len(orders),
                    "amount": sum(orders.mapped("amount_total")),
                },
                "payments_amount": sum(payments.mapped("amount")),
                "pay_later_amount": sum(pay_later_payments.mapped("amount")),
                "opening_notes": self.opening_notes,
                "default_cash_details": {
                    "name": default_cash_payment_method_id.name,
                    "amount": last_session.cash_register_balance_end_real
                    + total_default_cash_payment_amount
                    + sum(self.sudo().statement_line_ids.mapped("amount")),
                    "opening": last_session.cash_register_balance_end_real,
                    "payment_amount": total_default_cash_payment_amount,
                    "moves": cash_in_out_list,
                    "id": default_cash_payment_method_id.id,
                }
                if default_cash_payment_method_id
                else None,
                "other_payment_methods": [
                    {
                        "name": pm.name,
                        "amount": sum(
                            orders.payment_ids.filtered(
                                lambda p: p.payment_method_id == pm
                            ).mapped("amount")
                        ),
                        "number": len(
                            orders.payment_ids.filtered(
                                lambda p: p.payment_method_id == pm
                            )
                        ),
                        "id": pm.id,
                        "type": pm.type,
                    }
                    for pm in other_payment_method_ids
                ],
                "is_manager": self.user_has_groups("point_of_sale.group_pos_manager"),
                "amount_authorized_diff": self.config_id.amount_authorized_diff
                if self.config_id.set_maximum_difference
                else None,
            }

    def _validate_session(
        self,
        balancing_account=False,
        amount_to_balance=0,
        bank_payment_method_diffs=None,
    ):
        res = super(PosSession, self)._validate_session(
            balancing_account=balancing_account,
            amount_to_balance=amount_to_balance,
            bank_payment_method_diffs=bank_payment_method_diffs,
        )
        # recompute the cash_register_balance_start for the next opened sessions
        opened_sessions = self.search(
            [
                ("config_id", "=", self.config_id.id),
                ("state", "!=", "closed"),
                ("start_at", ">", self.start_at),
            ]
        )
        for session in opened_sessions:
            last_session = self.search(
                [
                    ("config_id", "=", session.config_id.id),
                    ("start_at", "<", session.start_at),
                ],
                limit=1,
            )
            session.cash_register_balance_start = (
                last_session.cash_register_balance_end_real
            )  # defaults to 0 if lastsession is empty
        return res

    def open_frontend_cb(self):
        if not self.ids:
            return {}
        return self.config_id.with_context(session_id=self.ids).open_ui()
