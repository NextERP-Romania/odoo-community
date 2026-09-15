import json

from odoo import http
from odoo.http import request

from odoo.addons.point_of_sale.controllers.main import PosController


class NexterpPosController(PosController):
    @http.route(
        ["/pos/ui/<config_id>", "/pos/ui/<config_id>/<path:subpath>"],
        auth="user",
        type="http",
    )
    def pos_web(self, config_id=False, from_backend=False, subpath=None, **k):
        """Render the session named in the URL, not the register's current one.

        Core resolves the session from the config, which answers "the one
        open right now" -- ambiguous once several are. A register running
        more than one session links each of them with its own id, and that is
        the session to render. Everything else falls through to core.
        """
        if k.get("session_id"):
            pos_session = request.env["pos.session"].browse(int(k.get("session_id")))
            pos_config = pos_session.config_id
            # The POS only works in one company,
            # so we enforce the one of the session in the context
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
            session_info["nomenclature_id"] = pos_session.company_id.nomenclature_id.id
            session_info["fallback_nomenclature_id"] = (
                pos_session.config_id.fallback_nomenclature_id.id
            )
            context = {
                "from_backend": 1 if from_backend else 0,
                "use_pos_fake_tours": True if k.get("tours", False) else False,
                "session_info": session_info,
                "pos_session_id": pos_session.id,
                "pos_config_id": pos_session.config_id.id,
                "access_token": pos_session.config_id.access_token,
                "last_data_change": pos_session.config_id.last_data_change.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "urls_to_cache": json.dumps(
                    pos_config._get_url_to_cache(request.session.debug)
                ),
            }
            response = request.render("point_of_sale.index", context)
            response.headers["Cache-Control"] = "no-store"
            return response
        else:
            return super().pos_web(
                config_id=config_id, from_backend=from_backend, subpath=subpath, **k
            )
