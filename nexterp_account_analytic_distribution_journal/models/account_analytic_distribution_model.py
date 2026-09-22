# Copyright 2026 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import api, fields, models


class AccountAnalyticDistributionModel(models.Model):
    _inherit = "account.analytic.distribution.model"

    journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        ondelete="cascade",
        check_company=True,
        index=True,
        help="Pin this distribution model to a specific journal. Models "
        "pinned to a journal are only applied to lines posted in that "
        "journal; lines from any other journal ignore them.",
    )

    # NOTA (migrare 17.0 -> 19.0)
    # Pe 17.0 era de ajuns sa declaram campul: motorul de potrivire
    # (`_get_distribution` -> `_get_fields_to_check` / `_check_score`) enumera
    # automat TOATE campurile non-manuale ale modelului si le puncta, asa ca
    # `journal_id` intra singur in scor.
    #
    # Pe 19.0 punctarea a disparut. `_get_applicable_models` construieste un
    # domeniu doar din cheile primite in `vals`, completate cu
    # `_get_default_search_domain_vals()`, iar rezultatele tuturor modelelor
    # aplicabile se combina pe planuri analitice radacina.
    #
    # Sunt deci necesare doua lucruri, altfel campul ramane decorativ:
    #   1. `journal_id` in valorile implicite -- fara el nu se genereaza nicio
    #      conditie pe jurnal, deci un model fixat pe un jurnal s-ar aplica
    #      oricarei linii;
    #   2. `journal_id` in argumentele trimise de `account.move.line`
    #      (vezi account_move_line.py) -- fara el domeniul ar fi mereu
    #      `journal_id in [False, False]`, adica exact invers: modelele fixate
    #      pe jurnal nu s-ar aplica niciodata.
    #
    # `_create_domain` din core trateaza generic orice cheie ca
    # `(fname, 'in', [value, False])`, deci nu e nevoie sa o suprascriem.

    @api.model
    def _get_default_search_domain_vals(self):
        return {
            **super()._get_default_search_domain_vals(),
            "journal_id": False,
        }
