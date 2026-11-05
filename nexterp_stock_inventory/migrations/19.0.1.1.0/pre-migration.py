# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).


def migrate(cr, version):
    """Inventory lines become required to belong to an inventory.

    Lines left without one (their inventory was deleted before the cascade
    existed) carry nothing that is booked, so they are dropped; inventories
    without a company get the company of their lines, or the main company.
    """
    cr.execute("DELETE FROM l10n_ro_stock_inventory_line WHERE inventory_id IS NULL")
    cr.execute(
        """
        UPDATE l10n_ro_stock_inventory inv
           SET company_id = COALESCE(
                (SELECT line.company_id
                   FROM l10n_ro_stock_inventory_line line
                  WHERE line.inventory_id = inv.id
                    AND line.company_id IS NOT NULL
                  LIMIT 1),
                (SELECT id FROM res_company ORDER BY id LIMIT 1))
         WHERE inv.company_id IS NULL
        """
    )
