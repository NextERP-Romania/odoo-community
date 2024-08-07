# Copyright 2024 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/16.0/legal/licenses/licenses.html#).

from odoo import _, api, models
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"

    @api.depends("session_ids", "session_ids.state")
    def _compute_current_session(self):
        """
        Compute the current session based on the context or params.
        If the context has a session_id,
        use it and store it to current_session_id / current_session_state.
        """
        params = self.env.context.get("params")
        session = False
        if params and (params.get("model") == "pos.session") and params.get("id"):
            session = self.env["pos.session"].browse(params.get("id"))
        elif self.env.context.get("session_id"):
            session = self.env["pos.session"].browse(self.env.context.get("session_id"))
        if session and len(session) == 1 and session.state != "closed":
            self.current_session_id = session.id
            self.current_session_state = session.state
        else:
            return super(PosConfig, self)._compute_current_session()

    def _action_to_open_ui(self):
        res = super(PosConfig, self)._action_to_open_ui()

        # get current session, raise error if there is a previous session not closed
        session = self.current_session_id
        not_closed_sesions = session.search(
            [
                ("config_id", "=", session.config_id.id),
                ("state", "!=", "closed"),
                ("start_at", "<", session.start_at),
            ]
        )
        if not_closed_sesions:
            raise ValidationError(
                _(
                    "You cannot open the current session because there is another \
                    previous session that is not closed."
                )
            )
        if res.get("url"):
            res["url"] += "&session_id=%s" % session.id
        return res
