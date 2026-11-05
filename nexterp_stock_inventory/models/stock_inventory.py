# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).


from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


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
        required=True,
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

    @api.depends("accounting_date")
    def _compute_name(self):
        for inventory in self:
            inventory.name = f"Inventory - {inventory.accounting_date}"

    # Fields that make up the stocktaking itself: frozen once it is validated.
    _LOCKED_FIELDS = {
        "accounting_date",
        "company_id",
        "location_ids",
        "product_ids",
        "inventory_line_ids",
        "inventory_lines_generated",
    }

    def _check_draft(self):
        if any(inventory.state != "draft" for inventory in self):
            raise UserError(
                self.env._(
                    "A validated inventory can no longer be changed: its count "
                    "has already been written into the stock."
                )
            )

    def write(self, vals):
        if self._LOCKED_FIELDS.intersection(vals) or (
            "state" in vals and vals["state"] != "done"
        ):
            self._check_draft()
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_done(self):
        if any(inventory.state == "done" for inventory in self):
            raise UserError(
                self.env._(
                    "A validated inventory cannot be deleted: it is the document "
                    "behind the stock adjustments it generated."
                )
            )

    def action_validate_inventory(self):
        self = self.with_context(nexterp_skip_inventory=True)
        self.ensure_one()
        inventory = self
        inventory._check_draft()
        lines = inventory.inventory_line_ids
        for line in lines.filtered(lambda line: not line.quant_id):
            # quants with nothing on hand are cleaned up by the scheduler
            line.quant_id = line._get_or_create_quant(
                line.location_id, line.product_id, line.product_lot_id
            )
        for line in lines:
            quant = line.quant_id.with_context(inventory_mode=True)
            # the count on the document is authoritative, even when goods have
            # moved since it was made (what Odoo calls an outdated quant)
            quant.write(
                {
                    "accounting_date": inventory.accounting_date,
                    "inventory_quantity": line.inventory_quantity,
                }
            )
            quant.inventory_diff_quantity = quant.inventory_quantity - quant.quantity
            line.write(
                {
                    "value": quant.value,
                    "quantity": quant.quantity,
                    "inventory_diff_quantity": line.inventory_quantity - quant.quantity,
                }
            )
        quants = lines.quant_id.with_context(inventory_mode=True)
        quants._apply_inventory()
        quants.inventory_quantity_set = False
        for line in lines:
            line.inventory_value = line.quant_id.value
            line.inventory_diff_value = line.inventory_value - line.value
        inventory.state = "done"

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
        inventory._check_draft()
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
        self.env["l10n.ro.stock.inventory.line"].create(inventory_line_vals)
        inventory.inventory_lines_generated = True
        inventory_quants = inventory.inventory_line_ids.mapped("quant_id")
        inventory_quants_zero = inventory_quants.filtered(
            lambda q: q.inventory_quantity == 0
        )
        inventory_quants_zero.with_context(inventory_mode=True).inventory_quantity = 0

    def action_clear_inventory_lines(self):
        self.ensure_one()
        inventory = self
        inventory._check_draft()
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
    inventory_id = fields.Many2one(
        "l10n.ro.stock.inventory", required=True, ondelete="cascade", index=True
    )
    state = fields.Selection(
        related="inventory_id.state",
        store=True,
    )
    accounting_date = fields.Date(
        related="inventory_id.accounting_date",
        store=True,
    )
    quant_id = fields.Many2one("stock.quant")
    # stored from the product: a validated line keeps its unit even after the
    # quant it counted has been cleaned up
    product_uom_id = fields.Many2one(
        string="UoM", related="product_id.uom_id", store=True
    )
    inventory_quantity = fields.Float(string="Counted Quantity")
    inventory_diff_quantity = fields.Float(string="Difference", readonly=True)
    quantity = fields.Float(string="On Hand Quantity", readonly=True)
    standard_price = fields.Float(readonly=True)
    value = fields.Monetary(readonly=True)
    inventory_value = fields.Monetary(readonly=True)
    inventory_diff_value = fields.Monetary(readonly=True)
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

    @api.model
    def _get_or_create_quant(self, location, product, lot):
        quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", location.id),
                ("product_id", "=", product.id),
                ("lot_id", "=", lot.id),
            ],
            limit=1,
        )
        if not quant:
            quant = (
                self.env["stock.quant"]
                .with_context(inventory_mode=True)
                .create(
                    {
                        "location_id": location.id,
                        "product_id": product.id,
                        "lot_id": lot.id,
                        "inventory_quantity": 0,
                    }
                )
            )
        return quant

    @api.constrains("product_id", "product_lot_id", "inventory_quantity")
    def _check_lot_for_tracked_product(self):
        # Adjustments made straight on the quants follow Odoo's own rules.
        if self.env.context.get("nexterp_inventory_from_quant"):
            return
        for line in self:
            # Counting down a quant that already has no lot is tolerated (Odoo
            # allows such quants); bringing goods in without a lot is not.
            if (
                line.product_id.tracking != "none"
                and not line.product_lot_id
                and line.product_id.uom_id.compare(
                    line.inventory_quantity, line.quant_id.quantity
                )
                > 0
            ):
                raise ValidationError(
                    self.env._(
                        "Product %(product)s is tracked by lot/serial number: "
                        "the inventory line needs one.",
                        product=line.product_id.display_name,
                    )
                )

    def _check_inventory_draft(self):
        if any(line.inventory_id.state == "done" for line in self):
            raise UserError(
                self.env._(
                    "The lines of a validated inventory can no longer be changed."
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Add possibility to create stock.quant directly from inventory line creation,
        in case quant doesn't exist for the given location/product/lot.
        """
        inventories = self.env["l10n.ro.stock.inventory"].browse(
            [vals["inventory_id"] for vals in vals_list if vals.get("inventory_id")]
        )
        inventories._check_draft()
        for vals in vals_list:
            if (
                not vals.get("quant_id")
                and vals.get("location_id")
                and vals.get("product_id")
            ):
                quant = self._get_or_create_quant(
                    self.env["stock.location"].browse(vals["location_id"]),
                    self.env["product.product"].browse(vals["product_id"]),
                    self.env["stock.lot"].browse(vals.get("product_lot_id") or []),
                )
                vals["quant_id"] = quant.id
        return super().create(vals_list)

    def write(self, vals):
        self._check_inventory_draft()
        if {"location_id", "product_id", "product_lot_id", "quant_id"}.intersection(
            vals
        ):
            for line in self.filtered("quant_id"):
                quant = line.quant_id
                if (
                    vals.get("location_id", quant.location_id.id)
                    != quant.location_id.id
                    or vals.get("product_id", quant.product_id.id)
                    != quant.product_id.id
                    or (vals.get("product_lot_id", quant.lot_id.id) or False)
                    != (quant.lot_id.id or False)
                    or vals.get("quant_id", quant.id) != quant.id
                ):
                    raise UserError(
                        self.env._(
                            "The location, product and lot of an inventory line "
                            "come from the quant it counts and cannot be changed; "
                            "delete the line and add a new one instead."
                        )
                    )
        res = super().write(vals)
        if "inventory_quantity" in vals:
            for line in self:
                quant = line.quant_id.with_context(inventory_mode=True)
                quant.inventory_quantity = line.inventory_quantity
                line.quantity = quant.quantity
                line.inventory_diff_quantity = quant.inventory_diff_quantity
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_done(self):
        self._check_inventory_draft()
