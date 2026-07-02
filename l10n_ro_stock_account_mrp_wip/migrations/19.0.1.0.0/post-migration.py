# Copyright 2026 NextERP Romania
# License LGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Reuse Odoo-native WIP fields.

Older versions of this module stored the WIP <-> manufacturing order link on
its own columns:
    - account_move.l10n_ro_wip_production_id      (many2one)
    - account_move_line.l10n_ro_wip_production_id (many2one)

Odoo 19 ``mrp_account`` provides a native many2many between ``account.move``
and ``mrp.production`` (relation table ``wip_move_production_rel``). We move the
legacy data into it and drop the obsolete columns.

The company-level WIP accounts kept the same field names as the native ones
(``account_production_wip_account_id`` / ``_overhead_account_id``), so their
data is preserved automatically and needs no migration here.
"""

import logging

_logger = logging.getLogger(__name__)


def _column_exists(cr, table, column):
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return bool(cr.fetchone())


def migrate(cr, version):
    if not version:
        return

    if _column_exists(cr, "account_move", "l10n_ro_wip_production_id"):
        _logger.info(
            "l10n_ro_stock_account_mrp_wip: migrating legacy WIP production "
            "link into native wip_move_production_rel"
        )
        cr.execute(
            """
            INSERT INTO wip_move_production_rel (production_id, move_id)
            SELECT am.l10n_ro_wip_production_id, am.id
            FROM account_move am
            WHERE am.l10n_ro_wip_production_id IS NOT NULL
              AND NOT EXISTS (
                  SELECT 1 FROM wip_move_production_rel rel
                  WHERE rel.production_id = am.l10n_ro_wip_production_id
                    AND rel.move_id = am.id
              )
            """
        )
        cr.execute("ALTER TABLE account_move DROP COLUMN l10n_ro_wip_production_id")

    if _column_exists(cr, "account_move_line", "l10n_ro_wip_production_id"):
        cr.execute(
            "ALTER TABLE account_move_line DROP COLUMN l10n_ro_wip_production_id"
        )
