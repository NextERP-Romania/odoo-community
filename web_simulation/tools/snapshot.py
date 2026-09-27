# Copyright (C) 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
"""Marking where the database stood before a simulation started."""

from odoo.tools import SQL


def take_snapshot(cr, registry, models):
    """Record the highest id of each watched table.

    Ids come from PostgreSQL sequences, which ignore transactions, so
    everything created afterwards lands above these marks.  That is a
    sharper filter than a timestamp: inside a single transaction ``now()``
    is frozen, so every row written there would share one ``create_date``.
    """
    snapshot = {}
    for model_name in models:
        model = registry.models.get(model_name)
        if model is None:
            continue
        table = model._table
        cr.execute(SQL("SELECT to_regclass(%s)", f"public.{table}"))
        if not cr.fetchone()[0]:
            continue
        cr.execute(SQL("SELECT max(id) FROM %s", SQL.identifier(table)))
        snapshot[model_name] = cr.fetchone()[0] or 0
    return snapshot
