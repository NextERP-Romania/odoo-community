import logging

from odoo import http
from odoo.http import request
from odoo.osv.expression import AND

from odoo.addons.point_of_sale.controllers.main import PosController

_logger = logging.getLogger(__name__)


class SessionPosController(PosController):
    @http.route(["/pos/web", "/pos/ui"], type="http", auth="user")
    def pos_web(self, config_id=False, **k):
        is_internal_user = request.env.user.has_group("base.group_user")
        if not is_internal_user:
            return request.not_found()
        if config_id:
            pos_config = request.env["pos.config"].sudo().browse(int(config_id))
        if k.get("session_id"):
            pos_session = (
                request.env["pos.session"].sudo().browse(int(k.get("session_id")))
            )
        else:
            domain = [
                ("state", "in", ["opening_control", "opened"]),
                ("user_id", "=", request.session.uid),
                ("rescue", "=", False),
            ]
            if config_id:
                domain = AND([domain, [("config_id", "=", int(config_id))]])
            pos_session = request.env["pos.session"].sudo().search(domain, limit=1)

            # The same POS session can be opened by a different user =>
            # search without restricting to
            # current user. Note: the config must be explicitly given
            # to avoid fallbacking on a random
            # session.
            if not pos_session and config_id:
                domain = [
                    ("state", "in", ["opening_control", "opened"]),
                    ("rescue", "=", False),
                    ("config_id", "=", int(config_id)),
                ]
                pos_session = request.env["pos.session"].sudo().search(domain, limit=1)
        if not pos_session or config_id and not pos_config.active:
            return request.redirect("/web#action=point_of_sale.action_client_pos_menu")
        # The POS only work in one company, so we enforce the one of the session in the context
        company = pos_session.company_id
        session_info = request.env["ir.http"].session_info()
        session_info["user_context"]["allowed_company_ids"] = company.ids
        session_info["user_companies"] = {
            "current_company": company.id,
            "allowed_companies": {
                company.id: session_info["user_companies"]["allowed_companies"][
                    company.id
                ]
            },
        }
        context = {
            "session_info": session_info,
            "login_number": pos_session.login(),
            "pos_session_id": pos_session.id,
        }
        response = request.render("point_of_sale.index", context)
        response.headers["Cache-Control"] = "no-store"
        return response
