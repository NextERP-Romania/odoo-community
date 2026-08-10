from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    remove_non_deductible_percent(env)


def remove_non_deductible_percent(env):
    if not openupgrade.column_exists(env.cr, "fleet_vehicle", "non_deductible_percent"):
        return
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE fleet_vehicle
        SET l10n_ro_nondeductible_percent = CASE
            WHEN non_deductible_percent=50 THEN '50'
            WHEN non_deductible_percent=100 THEN '100'
            ELSE '0'
        END
        """,
    )
    # openupgrade.remove_columns(env.cr, [("fleet_vehicle", "non_deductible_percent")])
