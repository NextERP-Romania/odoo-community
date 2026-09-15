# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    pos_multi_session = fields.Boolean(
        string="Multiple Open Sessions",
        help="Allow several sessions to stay open at once on this register. "
        "They must then be closed oldest first, so the cash carries over in "
        "the order the days happened.",
    )

    @api.depends("session_ids", "session_ids.state")
    def _compute_current_session(self):
        """Point at the OLDEST open session, not the newest.

        Core assumes one session at a time, so "current" means the last one
        created. With several open at once that is the wrong end: the register
        is still working through the oldest day, and that is the session a
        cashier reopening the till must land in. An explicit ``session_id`` in
        the context still wins -- that is someone asking for a named session.
        """
        res = super()._compute_current_session()
        for pos_config in self:
            if not pos_config.pos_multi_session:
                continue
            session = pos_config._pos_multi_session_context_session()
            if not session:
                session = pos_config._pos_multi_session_oldest_open()
            if session:
                pos_config.current_session_id = session.id
                pos_config.current_session_state = session.state
        return res

    def _pos_multi_session_context_session(self):
        """The session the context names, when it belongs to this register."""
        self.ensure_one()
        session_id = self.env.context.get("session_id")
        if not session_id:
            return self.env["pos.session"]
        session = self.env["pos.session"].browse(session_id)
        return session if session.config_id == self else self.env["pos.session"]

    def _pos_multi_session_oldest_open(self):
        """The open session that started first; the register's oldest day.

        A session created but never opened has no ``start_at`` yet and cannot
        be ordered by it, so those fall back to creation order.
        """
        self.ensure_one()
        open_sessions = self.session_ids.filtered(lambda s: s.state != "closed")
        started = open_sessions.filtered(lambda s: s.start_at)
        if started:
            return started.sorted(key=lambda s: (s.start_at, s.id))[0]
        # Sessions created in the same second share a ``create_date``, and the
        # recordset arrives newest first, so the id has to break the tie or
        # the youngest would win.
        return open_sessions.sorted(key=lambda s: (s.create_date, s.id))[:1]

    def get_statistics_for_session(self, session):
        """Report on the oldest open session, the one the register is on."""
        self.ensure_one()
        if self.pos_multi_session:
            oldest = self._pos_multi_session_oldest_open()
            if oldest:
                session = oldest
        return super().get_statistics_for_session(session)

    def _action_to_open_ui(self):
        """Refuse to open a session while an older one is still open.

        Closing out of order would carry the wrong cash balance forward: each
        session starts from the real end balance of the one before it, and
        that balance does not exist until that session is closed.
        """
        res = super()._action_to_open_ui()
        session = self.current_session_id
        if not session.config_id.pos_multi_session:
            return res
        older_open = session.search_count(
            [
                ("config_id", "=", session.config_id.id),
                ("state", "!=", "closed"),
                ("start_at", "<", session.start_at),
            ],
            limit=1,
        )
        if older_open:
            raise ValidationError(
                self.env._(
                    "An earlier session of this Point of Sale is still open. "
                    "Sessions are closed oldest first, so that one has to be "
                    "closed before this can be opened."
                )
            )
        if res.get("url"):
            res["url"] += f"&session_id={session.id}"
        return res
