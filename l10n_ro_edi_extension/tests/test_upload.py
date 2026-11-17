# Copyright (C) 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""Uploading an e-Factura: which ``standard`` ANAF is told, and what the user
reads when ANAF refuses it.

The replies below are the ones ANAF's test SPV gave for a storno credit note
(an <Invoice> 380 with negative values) uploaded as ``CN`` and as ``UBL``.
"""

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.l10n_ro_edi_extension.models import utils

INVOICE = b'<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"/>'
CREDIT_NOTE = (
    b'<CreditNote xmlns="urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"/>'
)
REFUSED = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    b'<header xmlns="mfp:anaf:dgti:spv:respUploadFisier:v1" '
    b'dateResponse="202611172053" ExecutionStatus="1">\n'
    b'    <Errors errorMessage="Fisierul transmis nu este valid. '
    b"cvc-elt.1.a: Cannot find the declaration of element 'Invoice'.\"/>\n"
    b"</header>"
)
ACCEPTED = (
    b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    b'<header xmlns="mfp:anaf:dgti:spv:respUploadFisier:v1" '
    b'dateResponse="202611172053" ExecutionStatus="0" '
    b'index_incarcare="5036467404"/>'
)


@tagged("post_install", "-at_install")
class TestUpload(TransactionCase):
    def _upload(self, xml, reply):
        company = self.env.company
        company.vat = "RO26207450"
        with patch.object(
            utils, "make_efactura_request", return_value={"content": reply}
        ) as request:
            result = utils._request_ciusro_upload(company, xml)
        return result, request.call_args.kwargs["params"]

    def test_a_storno_invoice_is_uploaded_as_ubl(self):
        _result, params = self._upload(INVOICE, ACCEPTED)
        self.assertEqual(params["standard"], "UBL")

    def test_a_credit_note_is_uploaded_as_cn(self):
        _result, params = self._upload(CREDIT_NOTE, ACCEPTED)
        self.assertEqual(params["standard"], "CN")

    def test_the_index_is_returned(self):
        result, _params = self._upload(INVOICE, ACCEPTED)
        self.assertEqual(result, {"key_loading": "5036467404"})

    def test_anaf_reason_reaches_the_user(self):
        """Native looked in the wrong namespace and returned ''."""
        result, _params = self._upload(INVOICE, REFUSED)
        self.assertIn("Cannot find the declaration of element", result["error"])
