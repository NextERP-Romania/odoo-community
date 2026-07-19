# Copyright 2026 NextERP Romania SRL

from odoo.addons.l10n_ro_edi_stock.models.etransport_api import ETransportAPI


class ETransportAPIExtra(ETransportAPI):
    """Extends the official API with the LIST and TRANSPORTER INFO services.

    Reuses _make_etransport_request for oauth2 authentication.
    """

    def _make_etransport_request(
        self, company, endpoint, method, session=None, data=None
    ):
        # OVERRIDE: the base only maps HTTP 404/403/401/204 and then assumes the
        # body always contains 'ExecutionStatus'. Any other shape (e.g. a gateway
        # error body, or JSON without that key) raises KeyError and crashes the
        # caller. Catch it and return a normal error dict instead.
        try:
            return super()._make_etransport_request(
                company=company,
                endpoint=endpoint,
                method=method,
                session=session,
                data=data,
            )
        except (KeyError, ValueError, TypeError) as err:
            return {
                "error": self.env._("Unexpected response from ANAF eTransport: %s", err)
            }

    def get_list(self, company_id, days=60, session=None):
        cif = company_id.vat.replace("RO", "")
        return self._make_etransport_request(
            company=company_id,
            endpoint=f"lista/{days}/{cif}",
            method="get",
            session=session,
        )

    def get_transporter_info(
        self, company_id, cui_op, cui_decl=None, uit=None, ref_decl=None, session=None
    ):
        params = [f"cui_op={cui_op}"]
        if cui_decl:
            params.append(f"cui_decl={cui_decl}")
        if uit:
            params.append(f"uit={uit}")
        if ref_decl:
            params.append(f"ref_decl={ref_decl}")
        return self._make_etransport_request(
            company=company_id,
            endpoint=f"info?{'&'.join(params)}",
            method="get",
            session=session,
        )
