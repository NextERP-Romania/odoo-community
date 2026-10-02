# Copyright (C) 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
"""What the simulated flow produced, on stock and on the books.

The result is read in two steps, because of when it has to happen: it must
be read *before* the savepoint is rolled back and written *after*, or the
result would vanish along with what it describes.  So :meth:`_collect`
returns plain values and :meth:`_materialize` turns them into records, and
nothing in between holds on to a row that is about to disappear.

Rows written anywhere in the transaction carry its timestamp, which is what
separates the flow's work from what was already in the database.  Stock
quants are the exception: they are updated rather than created, so they are
read as they stand for the products and locations the moves touched.
"""

from odoo import api, fields, models

#: Documents worth listing on their own, in the order they read best.
DOCUMENT_MODELS = (
    "purchase.order",
    "sale.order",
    "stock.picking",
    "mrp.production",
    "stock.scrap",
    "stock.landed.cost",
    "pos.session",
    "pos.order",
    "account.move",
    "account.payment",
    "stock.lot",
)

#: Everything to put a mark on before the operations start.
WATCHED_MODELS = DOCUMENT_MODELS + (
    "stock.move",
    "stock.move.line",
    "account.move.line",
    "product.value",
    "stock.quant",
)


class SimulationResult(models.TransientModel):
    _name = "web.simulation.result"
    _description = "Simulation Result"

    origin_label = fields.Char(readonly=True)
    error = fields.Text(readonly=True)
    pending_action = fields.Char(readonly=True)
    document_line_ids = fields.One2many(
        "web.simulation.result.document", "report_id", readonly=True
    )
    move_line_ids = fields.One2many(
        "web.simulation.result.move", "report_id", readonly=True
    )
    quant_line_ids = fields.One2many(
        "web.simulation.result.quant", "report_id", readonly=True
    )
    account_line_ids = fields.One2many(
        "web.simulation.result.account", "report_id", readonly=True
    )
    account_summary_ids = fields.One2many(
        "web.simulation.result.account.summary", "report_id", readonly=True
    )
    is_balanced = fields.Boolean(readonly=True)
    total_debit = fields.Float(readonly=True)
    total_credit = fields.Float(readonly=True)

    # -- reading --------------------------------------------------------

    @api.model
    def _collect(self, snapshot):
        """Return, as plain values, everything created above ``snapshot``."""
        data = {"documents": [], "moves": [], "quants": []}
        data["documents"] = self._collect_documents(snapshot)
        moves, data["moves"] = self._collect_moves(snapshot)
        data["quants"] = self._collect_quants(moves)
        data.update(self._collect_accounting(snapshot))
        return data

    @api.model
    def _new_records(self, model_name, snapshot):
        """Return what this transaction created or changed in ``model_name``.

        ``write_date`` is stamped with ``cr.now()``, the transaction's
        timestamp, so a row written anywhere in the transaction carries
        exactly that value and nothing older does.  Connections run in
        repeatable read, so what other people commit meanwhile is not even
        visible, let alone mistaken for ours.

        This catches changes, not only creations, which is what a simulation
        needs: validating a transfer that already exists does not create a
        stock move, it finishes one.  The id mark stays as the fallback for
        the few models that keep no write date.
        """
        if model_name not in self.env:
            return None
        model = self.env[model_name].sudo().with_context(active_test=False)
        domain = []  # filled in below; never searched while still empty
        if model._log_access:
            domain = [("write_date", ">=", self.env.cr.now())]
        mark = snapshot.get(model_name)
        if mark is not None:
            domain = (
                ["|", *domain, ("id", ">", mark)] if domain else [("id", ">", mark)]
            )
        if not domain:
            return None
        # pylint: disable=no-search-all
        return model.search(domain, order="id")

    @api.model
    def _collect_documents(self, snapshot):
        values = []
        for model_name in DOCUMENT_MODELS:
            records = self._new_records(model_name, snapshot)
            if not records:
                continue
            description = self.env["ir.model"]._get(model_name).name
            sequence = DOCUMENT_MODELS.index(model_name)
            for record in records:
                values.append(
                    {
                        "sequence": sequence,
                        "model_name": model_name,
                        "model_description": description,
                        "name": record.display_name,
                        "state": self._state_of(record),
                        "amount": self._amount_of(record),
                        "res_id": record.id,
                    }
                )
        return values

    @api.model
    def _collect_moves(self, snapshot):
        moves = self._new_records("stock.move", snapshot)
        if not moves:
            return self.env["stock.move"], []
        moves = moves.filtered(lambda move: move.state == "done")
        has_value = "value" in self.env["stock.move"]._fields
        values = [
            {
                "product_id": move.product_id.id,
                "reference": move.reference or move.display_name,
                "location_id": move.location_id.id,
                "location_dest_id": move.location_dest_id.id,
                "quantity": move.quantity,
                "uom_name": move.product_id.uom_id.name,
                "value": move.value if has_value else 0.0,
            }
            for move in moves
        ]
        return moves, values

    @api.model
    def _collect_quants(self, moves):
        """Where the products stand now, not only what moved.

        A move tells the delta; the question is usually the balance, and for
        a FIFO product the balance is where the remaining layers show up.
        """
        if not moves:
            return []
        products = moves.product_id
        locations = (moves.location_id | moves.location_dest_id).filtered(
            lambda location: location.usage in ("internal", "transit")
        )
        if not products or not locations:
            return []
        # The quant's value is computed from the product's total value, and
        # that was read before the flow moved anything.  Reading it now
        # without dropping the cache gives the value the product had when
        # the request started, which is usually zero.
        self.env.flush_all()
        self.env.invalidate_all()
        quants = (
            self.env["stock.quant"]
            .sudo()
            .search(
                [
                    ("product_id", "in", products.ids),
                    ("location_id", "in", locations.ids),
                ]
            )
        )
        has_value = "value" in self.env["stock.quant"]._fields
        moved = self._moved_quantities(moves)
        values = []
        for quant in quants:
            change = moved.get((quant.product_id.id, quant.location_id.id), 0.0)
            values.append(
                {
                    "product_id": quant.product_id.id,
                    "location_id": quant.location_id.id,
                    "lot_name": quant.lot_id.name or "",
                    "quantity_before": quant.quantity - change,
                    "quantity_change": change,
                    "quantity": quant.quantity,
                    "uom_name": quant.product_id.uom_id.name,
                    "value": quant.value if has_value else 0.0,
                }
            )
        return values

    @api.model
    def _moved_quantities(self, moves):
        """How much the flow itself put in or took out of each place.

        Without this the balance reads as if the flow had produced all of
        it, when most of the time it sits on top of stock that was already
        there.
        """
        moved = {}
        for move in moves:
            product = move.product_id.id
            if move.location_dest_id.usage in ("internal", "transit"):
                key = (product, move.location_dest_id.id)
                moved[key] = moved.get(key, 0.0) + move.quantity
            if move.location_id.usage in ("internal", "transit"):
                key = (product, move.location_id.id)
                moved[key] = moved.get(key, 0.0) - move.quantity
        return moved

    @api.model
    def _collect_accounting(self, snapshot):
        lines = self._new_records("account.move.line", snapshot)
        if not lines:
            return {"account_lines": [], "account_summary": []}
        account_lines = []
        by_account = {}
        for line in lines:
            account_lines.append(
                {
                    "move_name": line.move_id.display_name,
                    "move_state": line.move_id.state,
                    "date": line.date,
                    "account_id": line.account_id.id,
                    "name": line.name or "",
                    "partner_id": line.partner_id.id,
                    "debit": line.debit,
                    "credit": line.credit,
                }
            )
            if line.parent_state != "posted":
                # The lines of a draft entry are real rows but they are
                # not accounting yet; counting them would answer "what
                # does this post" with something that has not posted.
                continue
            debit, credit = by_account.get(line.account_id, (0.0, 0.0))
            by_account[line.account_id] = (debit + line.debit, credit + line.credit)

        summary = sorted(by_account.items(), key=lambda item: item[0].code or "")
        total_debit = sum(debit for _account, (debit, _credit) in summary)
        total_credit = sum(credit for _account, (_debit, credit) in summary)
        return {
            "account_lines": account_lines,
            "account_summary": [
                {"account_id": account.id, "debit": debit, "credit": credit}
                for account, (debit, credit) in summary
            ],
            "total_debit": total_debit,
            "total_credit": total_credit,
            "is_balanced": self.env.company.currency_id.is_zero(
                total_debit - total_credit
            ),
        }

    # -- writing --------------------------------------------------------

    @api.model
    def _materialize(self, data):
        """Turn collected values into records, after any rollback."""
        report = self.create(
            {
                "origin_label": data.get("origin_label", ""),
                "error": data.get("error", False),
                "pending_action": data.get("pending_action", False),
                "total_debit": data.get("total_debit", 0.0),
                "total_credit": data.get("total_credit", 0.0),
                "is_balanced": data.get("is_balanced", True),
            }
        )
        self._create_lines("web.simulation.result.document", report, data["documents"])
        self._create_lines("web.simulation.result.move", report, data["moves"])
        self._create_lines("web.simulation.result.quant", report, data["quants"])
        self._create_lines(
            "web.simulation.result.account", report, data.get("account_lines", [])
        )
        self._create_lines(
            "web.simulation.result.account.summary",
            report,
            data.get("account_summary", []),
        )
        return report

    @api.model
    def _create_lines(self, model_name, report, values, extra=None):
        if not values:
            return
        values = [dict(vals, report_id=report.id, **(extra or {})) for vals in values]
        self._drop_vanished_references(model_name, values)
        self.env[model_name].create(values)

    @api.model
    def _drop_vanished_references(self, model_name, values):
        """Forget links to records the rollback took away.

        Products, locations and accounts are normally older than the
        simulation and survive it, but an operation that created one would
        otherwise leave the result pointing at a row that no longer exists.
        """
        model = self.env[model_name]
        for field_name, field in model._fields.items():
            if field.type != "many2one" or field_name == "report_id":
                continue
            ids = {vals[field_name] for vals in values if vals.get(field_name)}
            if not ids:
                continue
            alive = set(self.env[field.comodel_name].browse(ids).exists().ids)
            for vals in values:
                if vals.get(field_name) and vals[field_name] not in alive:
                    vals[field_name] = False

    # -- small helpers --------------------------------------------------

    @api.model
    def _state_of(self, record):
        for field_name in ("state", "status"):
            if field_name in record._fields:
                return record._fields[field_name].convert_to_export(
                    record[field_name], record
                )
        return ""

    @api.model
    def _amount_of(self, record):
        for field_name in ("amount_total", "amount_untaxed", "amount"):
            if field_name in record._fields:
                return record[field_name]
        return 0.0
