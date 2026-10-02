# Copyright (C) 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
"""Keep module surgery out of a simulation.

Installing or upgrading inside a simulation would build a registry that
describes tables and columns the rollback then takes away, leaving the
server talking about a schema that no longer exists.  There is no safe way
to undo that, so it is refused up front - and these are header buttons of
the Apps form, so a simulation could otherwise reach them.
"""

from odoo import api, models
from odoo.exceptions import UserError

from ..tools import numbering


class IrModuleModule(models.Model):
    _inherit = "ir.module.module"

    @api.model
    def _reject_in_simulation(self):
        if numbering.simulating():
            raise UserError(
                self.env._(
                    "Modules cannot be installed, upgraded or uninstalled in "
                    "a simulation: schema changes cannot be rolled back with "
                    "the rest."
                )
            )

    def button_immediate_install(self):
        self._reject_in_simulation()
        return super().button_immediate_install()

    def button_immediate_upgrade(self):
        self._reject_in_simulation()
        return super().button_immediate_upgrade()

    def button_immediate_uninstall(self):
        self._reject_in_simulation()
        return super().button_immediate_uninstall()
