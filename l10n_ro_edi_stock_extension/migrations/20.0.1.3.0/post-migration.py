# Copyright 2026 NextERP Romania SRL
"""Make sure the absorbed module is gone once this module has been loaded.

The merge in the pre-migration script already removes the
``l10n_ro_edi_stock_batch_extension`` record, so this is only a fallback for a
database where the merge did not run (an upgrade that skipped this version, a
module list rebuilt from an addons path that still carries the old directory).

The uninstall is deliberately conditional: it only happens once the old module
owns no ``ir_model_data`` row any more. Uninstalling it while it still owns its
records would drop the very columns this module has just taken over.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

OLD_MODULE = "l10n_ro_edi_stock_batch_extension"


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    module = env["ir.module.module"].search([("name", "=", OLD_MODULE)])
    if not module:
        return

    cr.execute("SELECT count(*) FROM ir_model_data WHERE module = %s", (OLD_MODULE,))
    if cr.fetchone()[0]:
        _logger.warning(
            "%s still owns database records and was left installed; "
            "uninstalling it now would drop the columns %s took over.",
            OLD_MODULE,
            "l10n_ro_edi_stock_extension",
        )
        return

    if module.state in ("installed", "to upgrade", "to remove", "to install"):
        module.module_uninstall()
    module.unlink()
    _logger.info("%s uninstalled and removed from the module list", OLD_MODULE)
