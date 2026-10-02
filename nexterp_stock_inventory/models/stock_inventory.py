# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).


from odoo import api, fields, models
from odoo.tools.float_utils import float_is_zero


class StockInventory(models.Model):
    _name = "l10n.ro.stock.inventory"
    _description = "Stock Inventory"
    _order = "accounting_date desc"

    name = fields.Char(
        compute="_compute_name",
        store=True,
    )
    accounting_date = fields.Date(default=fields.Date.context_today, required=True)
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
    )
    inventory_line_ids = fields.One2many(
        "l10n.ro.stock.inventory.line",
        "inventory_id",
    )
    inventory_lines_generated = fields.Boolean(default=False)
    location_ids = fields.Many2many(
        "stock.location",
        domain="[('usage', '=', 'internal')]",
    )
    product_ids = fields.Many2many(
        "product.product",
        domain="[('type', '=', 'consu')]",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("done", "Done"),
        ],
        default="draft",
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        store=True,
    )
    # Data printed on the inventory report (Proces verbal de inventariere)
    decision_number = fields.Char(
        help="Number of the decision appointing the inventory commission.",
    )
    commission_ids = fields.One2many(
        "l10n.ro.stock.inventory.commission",
        "inventory_id",
        string="Inventory Commission",
    )
    conclusions = fields.Text(
        help="Conclusions and proposals of the commission, printed at the "
        "end of the inventory report.",
    )
    surplus_value = fields.Monetary(
        compute="_compute_difference_values",
        help="Total value of the positive differences (surpluses).",
    )
    shortage_value = fields.Monetary(
        compute="_compute_difference_values",
        help="Total value of the negative differences (shortages), as a "
        "positive amount.",
    )
    difference_value = fields.Monetary(
        compute="_compute_difference_values",
        help="Net value of the inventory differences: surpluses less shortages.",
    )

    @api.depends("inventory_line_ids.inventory_diff_value")
    def _compute_difference_values(self):
        for inventory in self:
            values = inventory.inventory_line_ids.mapped("inventory_diff_value")
            surplus = sum(value for value in values if value > 0)
            shortage = -sum(value for value in values if value < 0)
            inventory.surplus_value = surplus
            inventory.shortage_value = shortage
            inventory.difference_value = surplus - shortage

    @api.depends("accounting_date")
    def _compute_name(self):
        for inventory in self:
            inventory.name = f"Inventory - {inventory.accounting_date}"

    def action_validate_inventory(self):
        self = self.with_context(nexterp_skip_inventory=True)
        self.ensure_one()
        inventory = self
        for line in inventory.inventory_line_ids:
            quant = line.quant_id.with_context(inventory_mode=True)
            quant.write(
                {
                    "accounting_date": inventory.accounting_date,
                }
            )
            line.value = quant.value
            line.quantity = quant.quantity
            line.inventory_diff_quantity = line.inventory_quantity - line.quantity
            line._update_diff_values()
            quant.action_apply_inventory()
            line.inventory_value = quant.value
            line.inventory_diff_value = line.inventory_value - line.value

        inventory.state = "done"

    def _report_lines(self):
        """Lines with a difference, sorted the way they are printed.

        The inventory report only lists the products whose counted quantity
        differs from the quantity on hand; the lines that merely confirm the
        stock are summarised by the totals.
        """
        self.ensure_one()
        precision = self.env["decimal.precision"].precision_get("Product Unit")
        lines = self.inventory_line_ids.filtered(
            lambda line: not float_is_zero(
                line.inventory_diff_quantity, precision_digits=precision
            )
        )
        return lines.sorted(
            lambda line: (
                line.location_id.complete_name or "",
                line.product_id.display_name or "",
            )
        )

    def _report_summary_by_location(self):
        """Per-location totals of the differences, for the report summary.

        :return: list of dicts with the location, the surplus value, the
            shortage value (positive) and the net difference.
        """
        self.ensure_one()
        summary = {}
        for line in self._report_lines():
            values = summary.setdefault(
                line.location_id,
                {"location": line.location_id, "surplus": 0.0, "shortage": 0.0},
            )
            value = line._report_diff_value()
            if value > 0:
                values["surplus"] += value
            else:
                values["shortage"] -= value
        for values in summary.values():
            values["difference"] = values["surplus"] - values["shortage"]
        return sorted(
            summary.values(), key=lambda values: values["location"].complete_name or ""
        )

    def _report_totals(self):
        """Surplus, shortage and net of the printed document.

        Built from the printed value of each line rather than from the cost
        totals of the form: a location that carries its goods at another
        value - a shop holding them at shelf price - prints that value, and
        the tables have to add up to what they show.
        """
        self.ensure_one()
        surplus = shortage = 0.0
        for line in self._report_lines():
            value = line._report_diff_value()
            if value > 0:
                surplus += value
            else:
                shortage -= value
        return {
            "surplus": surplus,
            "shortage": shortage,
            "difference": surplus - shortage,
        }

    def action_print_inventory_report(self):
        return self.env.ref(
            "nexterp_stock_inventory.action_report_stock_inventory"
        ).report_action(self)

    def action_generate_inventory_lines(self, quants=False):
        """
        Generate inventory lines based on the current stock quants.

        :param quants: Optional recordset of stock.quant to process. If provided,
            inventory lines will be generated only for these quants.
            Otherwise, quants are automatically fetched from:
                - All internal locations of the current company, or
                - The locations explicitly selected on the inventory.
            If products are specified on the inventory, only quants
            matching those products are considered.

        Behavior:
            - The method can be safely called multiple times while the inventory
            is in 'draft' state.
            - It does NOT create duplicate lines for quants that already have
            corresponding inventory lines.
            - It creates new inventory lines only for newly discovered quants.
            - Existing lines are preserved.

        Data synchronization:
            - Inventory lines are initialized with the current quant data
            (quantity, inventory quantity, difference, and value).
            - The actual stock quantities are NOT updated at this stage.
            They are only applied when the inventory is validated.

        Rationale:
            The separation between line generation and validation allows the system
            to preserve the original on-hand quantities. This makes it possible to
            accurately compute and track the difference between:
                - The theoretical (on-hand) quantity before validation, and
                - The counted quantity entered during the inventory process.
        """
        self.ensure_one()
        inventory = self
        if not inventory.location_ids:
            locations = self.env["stock.location"].search(
                [
                    ("usage", "=", "internal"),
                    ("company_id", "=", inventory.company_id.id),
                ]
            )
        else:
            locations = inventory.location_ids
        if not quants:
            quants_domain = [
                ("location_id", "in", locations.ids),
                ("company_id", "=", inventory.company_id.id),
            ]
            if inventory.product_ids:
                quants_domain.append(("product_id", "in", inventory.product_ids.ids))
            quants = self.env["stock.quant"].search(quants_domain)

        inventory_quants = inventory.inventory_line_ids.mapped("quant_id")
        inventory_line_vals = []
        for line in inventory.inventory_line_ids:
            line.write(
                {
                    "value": line.quant_id.value,
                    "quantity": line.quant_id.quantity,
                    "inventory_diff_quantity": line.inventory_quantity
                    - line.quant_id.quantity,
                }
            )
            line._update_diff_values()
        for quant in quants:
            if quant in inventory_quants:
                # if the quant already has an inventory line, we skip it
                # because we don't want to create duplicate lines for the same quant
                continue
            # if quant doesn't exist in inventory lines,
            # we create and update inventory_line_ids accordingly
            inventory_line_vals.append(
                {
                    "inventory_id": inventory.id,
                    "location_id": quant.location_id.id,
                    "product_id": quant.product_id.id,
                    "product_lot_id": quant.lot_id.id,
                    "quant_id": quant.id,
                    "value": quant.value,
                    "inventory_quantity": quant.inventory_quantity,
                    "inventory_diff_quantity": quant.inventory_diff_quantity,
                    "quantity": quant.quantity,
                    "standard_price": quant.product_id.standard_price,
                }
            )
        new_lines = self.env["l10n.ro.stock.inventory.line"].create(inventory_line_vals)
        for line in new_lines:
            line._update_diff_values()
        inventory.inventory_lines_generated = True
        inventory_quants = inventory.inventory_line_ids.mapped("quant_id")
        inventory_quants_zero = inventory_quants.filtered(
            lambda q: q.inventory_quantity == 0
        )
        inventory_quants_zero.with_context(inventory_mode=True).inventory_quantity = 0

    def action_clear_inventory_lines(self):
        self.ensure_one()
        inventory = self
        inventory.inventory_line_ids.mapped(
            "quant_id"
        ).action_clear_inventory_quantity()
        inventory.inventory_line_ids.unlink()
        inventory.inventory_lines_generated = False


class StockInventoryLine(models.Model):
    _name = "l10n.ro.stock.inventory.line"
    _description = "Stock Inventory Line"
    _order = "inventory_id, location_id, product_id"

    company_id = fields.Many2one(
        related="inventory_id.company_id",
        store=True,
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        store=True,
    )
    inventory_id = fields.Many2one("l10n.ro.stock.inventory")
    state = fields.Selection(
        related="inventory_id.state",
        store=True,
    )
    accounting_date = fields.Date(
        related="inventory_id.accounting_date",
        store=True,
    )
    quant_id = fields.Many2one("stock.quant")
    # Odoo 20 renamed the uom field of the stock models to uom_id
    product_uom_id = fields.Many2one(string="UoM", related="quant_id.uom_id")
    inventory_quantity = fields.Float(string="Counted Quantity")
    inventory_diff_quantity = fields.Float(string="Difference", readonly=True)
    quantity = fields.Float(string="On Hand Quantity", readonly=True)
    standard_price = fields.Float(readonly=True)
    value = fields.Monetary(readonly=True)
    inventory_value = fields.Monetary(readonly=True)
    inventory_diff_value = fields.Monetary(
        readonly=True,
        help="Value of the difference, filled as soon as the quantity is "
        "counted and replaced by the value actually booked once the "
        "inventory is validated. A surplus is valued at the current cost, a "
        "shortage at the FIFO layers it consumes or at the standard / "
        "average price, so the figure does not move on validation.",
    )
    location_id = fields.Many2one(
        "stock.location",
        domain="[('usage', '=', 'internal')]",
        required=True,
    )
    product_id = fields.Many2one(
        "product.product",
        domain="[('type', '=', 'consu')]",
        required=True,
    )
    product_lot_id = fields.Many2one(
        "stock.lot", domain="[('product_id', '=', product_id)]"
    )

    _unique_inventory_line = models.Constraint(
        "unique(inventory_id, quant_id)",
        "Only one inventory line allowed per quant.",
    )

    # _sql_constraints = [
    #     (
    #         "unique_inventory_line",
    #         "UNIQUE(inventory_id, quant_id)",
    #         "Only one inventory line per quant.",
    #     ),
    # ]

    def _update_diff_values(self):
        """Fill in the valuation of the counted difference.

        Everything that values a difference goes through this one hook, so a
        module carrying more than the cost - the retail markup and the
        deferred VAT, for instance - fills its own columns at the same
        moments: when the lines are generated, when the count is edited and
        just before the adjustment is booked.
        """
        for line in self:
            line.inventory_diff_value = line._get_diff_value()

    def _get_diff_value(self):
        """Value the counted difference the way the adjustment will book it.

        This mirrors `stock.move._compute_value()`: a surplus comes in at the
        current cost, a shortage goes out at the FIFO layers it consumes when
        the product is costed that way, and at the standard / average price
        otherwise. Lot valuation is honoured when the product uses it. The
        estimate is therefore the amount the validation writes in
        `inventory_diff_value`, so the report shows the same figure before
        and after the inventory is validated.
        """
        self.ensure_one()
        quantity = self.inventory_diff_quantity
        if not quantity:
            return 0.0
        product = self.product_id
        lot = self.product_lot_id if product.lot_valuated else self.env["stock.lot"]
        if quantity < 0 and product.cost_method == "fifo":
            if lot or not product.lot_valuated:
                return -product._get_fifo_value(-quantity, lot=lot or None)
        price = lot.standard_price if lot else product.standard_price
        return quantity * price

    def _report_diff_value(self):
        """Value of the difference as the inventory report prints it.

        The booked cost difference, unless the goods are carried at another
        value - a shop holds them at shelf price, where the difference the
        shop answers for is the one on 371 - in which case the document is
        drawn at that value instead.
        """
        self.ensure_one()
        return self.inventory_diff_value

    def _report_unit_value(self):
        """Unit value that makes the printed difference add up.

        The standard price is the product's current cost, which under FIFO is
        rarely what the consumed layers cost, so the report prints the unit
        value implied by the difference instead.
        """
        self.ensure_one()
        if self.inventory_diff_quantity:
            return self._report_diff_value() / self.inventory_diff_quantity
        return self.standard_price

    @api.model_create_multi
    def create(self, vals_list):
        """
        Add possibility to create stock.quant directly from inventory line creation,
        in case quant doesn't exist for the given location/product/lot.
        """
        for vals in vals_list:
            if (
                not vals.get("quant_id")
                and vals.get("location_id")
                and vals.get("product_id")
            ):
                quant = self.env["stock.quant"].search(
                    [
                        ("location_id", "=", vals["location_id"]),
                        ("product_id", "=", vals["product_id"]),
                        ("lot_id", "=", vals.get("product_lot_id") or False),
                    ],
                    limit=1,
                )
                if quant:
                    vals["quant_id"] = quant.id
                else:
                    quant = (
                        self.env["stock.quant"]
                        .with_context(inventory_mode=True)
                        .create(
                            {
                                "location_id": vals["location_id"],
                                "product_id": vals["product_id"],
                                "lot_id": vals.get("product_lot_id") or False,
                                "inventory_quantity": 0,
                            }
                        )
                    )
                    vals["quant_id"] = quant.id
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "inventory_quantity" in vals:
            for line in self:
                quant = line.quant_id.with_context(inventory_mode=True)
                quant.inventory_quantity = line.inventory_quantity
                line.quantity = quant.quantity
                line.inventory_diff_quantity = quant.inventory_diff_quantity
                line._update_diff_values()
        return res


class StockInventoryCommission(models.Model):
    _name = "l10n.ro.stock.inventory.commission"
    _description = "Stock Inventory Commission Member"
    _order = "inventory_id, sequence, id"

    inventory_id = fields.Many2one(
        "l10n.ro.stock.inventory",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    user_id = fields.Many2one("res.users")
    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
        required=True,
    )
    job_position = fields.Char()
    role = fields.Selection(
        selection=[
            ("chairman", "Chairman"),
            ("member", "Member"),
            ("stock_keeper", "Stock Keeper"),
        ],
        default="member",
        required=True,
    )

    @api.depends("user_id")
    def _compute_name(self):
        for member in self:
            if member.user_id:
                member.name = member.user_id.name
