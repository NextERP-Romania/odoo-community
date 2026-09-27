# Copyright 2026 NextERP Romania SRL
"""Absorb ``l10n_ro_edi_stock_batch_extension`` into this module.

Odoo 20.0 merged ``l10n_ro_edi_stock_batch`` into ``l10n_ro_edi_stock`` (the
whole ``stock_picking_batch`` module became part of ``stock``), so the separate
batch extension has no base module left to extend and its content moved here.

Uninstalling the old module would drop the columns it owns (``batch_id`` on the
transport document lines and on the previous notifications, and the eTransport
fields on ``stock.picking.batch``), all of which this module now declares.  A
module merge hands those records over instead, so the columns survive and this
module simply takes ownership of them.
"""

from openupgradelib import openupgrade

OLD_MODULE = "l10n_ro_edi_stock_batch_extension"
NEW_MODULE = "l10n_ro_edi_stock_extension"

# The batch form view is the only view of the old module that survives the
# merge, under a new name.
OLD_BATCH_FORM = "view_picking_batch_form_l10n_ro_edi_stock_batch_extension"
NEW_BATCH_FORM = "view_picking_batch_form_l10n_ro_edi_stock_extension"


def migrate(cr, version):
    if not version:
        return

    cr.execute("SELECT 1 FROM ir_module_module WHERE name = %s", (OLD_MODULE,))
    if not cr.fetchone():
        return

    # Rename before merging so the merge re-owns the existing view record
    # instead of dropping it and letting this module create a new one.
    openupgrade.logged_query(
        cr,
        "UPDATE ir_model_data SET name = %s WHERE module = %s AND name = %s",
        (NEW_BATCH_FORM, OLD_MODULE, OLD_BATCH_FORM),
    )

    # Hands the XML ids, the fields and the module dependencies over to this
    # module and drops the old module record. The old module's other views only
    # existed to bolt ``batch_id`` onto views of this module, which now carry
    # the field directly; they end up parked under this module without being
    # reloaded, so Odoo's end-of-load cleanup (``ir.model.data._process_end``)
    # removes them.
    openupgrade.update_module_names(cr, [(OLD_MODULE, NEW_MODULE)], merge_modules=True)
