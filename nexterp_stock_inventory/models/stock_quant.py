# Copyright (C) 2022 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).


from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def action_apply_inventory(self):
        """
        Automatically create and validate inventory records when stock quants
        are applied outside of the l10n.ro.stock.inventory workflow.

        This method acts as an inverse synchronization mechanism between
        stock.quant and l10n.ro.stock.inventory. When quants are adjusted
        directly (bypassing the standard inventory model), it ensures that
        a corresponding inventory document is created to preserve accounting
        traceability.

        Context behavior:
            - If the context key 'nexterp_skip_inventory' is set to True,
            it means the system is already validating an inventory through
            the standard workflow. In this case, the method skips the custom
            inventory creation logic and simply calls super() to avoid
            duplicate inventory documents or recursive behavior.

        Processing logic:
            - Quants are grouped by accounting_date.
            - For each distinct accounting date:
                * A new l10n.ro.stock.inventory record is created.
                * The inventory includes:
                    - The accounting date (or today's date if missing),
                    - The company of the quants,
                    - All involved locations,
                    - All involved products.
                * Inventory lines are generated only for the affected quants.

            - After creating the inventories, the standard super()
            action_apply_inventory() logic is executed to apply
            stock adjustments.

        Post-processing:
            - For each generated inventory:
                * Line values are updated with the final quant values.
                * The value difference is computed.
                * The inventory is marked as 'done'.
        """
        if self.env.context.get("nexterp_skip_inventory"):
            return super().action_apply_inventory()
        InventoryObject = self.env["l10n.ro.stock.inventory"]
        inventories = self.env["l10n.ro.stock.inventory"]
        for accounting_date in list(set(self.mapped("accounting_date"))):
            if not accounting_date:
                accounting_date = fields.Date.context_today(self)
                quants = self.filtered(lambda q: not q.accounting_date)
            else:
                quants = self.filtered(lambda q: q.accounting_date == accounting_date)
            inventory = InventoryObject.create(
                {
                    "accounting_date": accounting_date,
                    "company_id": quants[0].company_id.id,
                    "location_ids": quants.mapped("location_id").ids,
                    "product_ids": quants.mapped("product_id").ids,
                }
            )

            inventory.action_generate_inventory_lines(quants=quants)
            inventories |= inventory

        res = super().action_apply_inventory()

        for inventory in inventories:
            for line in inventory.inventory_line_ids:
                line.inventory_value = line.quant_id.value
                line.inventory_diff_value = line.inventory_value - line.value
            inventory.state = "done"

        return res
