# Copyright (C) 2026 NextERP Romania SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
"""Where ``ir.sequence`` is taught to count locally during a simulation.

See :mod:`..tools.numbering` for why.  The numbers handed out are the ones
the documents would really get, which is the point of the exercise, and the
sequence is left exactly where it was.

Sequences set to *no gap* need nothing: they keep their counter in a table
row, so the rollback takes care of them.
"""

from odoo import models

from odoo.addons.base.models.ir_sequence import _predict_nextval

from ..tools import numbering


def _simulated_next_number(records, seq_id, increment):
    """Return the next number for ``seq_id``, or None when it is for real."""
    counters = numbering.counters()
    if counters is None:
        return None
    number = counters.get(seq_id)
    if number is None:
        number = _predict_nextval(records, seq_id)
    counters[seq_id] = number + increment
    return number


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    def _next_do(self):
        if self.implementation == "standard":
            number = _simulated_next_number(
                self, f"{self.id:03d}", self.number_increment
            )
            if number is not None:
                return self.get_next_char(number)
        return super()._next_do()


class IrSequenceDateRange(models.Model):
    _inherit = "ir.sequence.date_range"

    def _next(self):
        sequence = self.sequence_id
        if sequence.implementation == "standard":
            number = _simulated_next_number(
                self,
                f"{sequence.id:03d}_{self.id:03d}",
                sequence.number_increment,
            )
            if number is not None:
                return sequence.get_next_char(number)
        return super()._next()
