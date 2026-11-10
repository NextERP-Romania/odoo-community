# Copyright 2026 NextERP Romania SRL
# License AGPL-3.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).
"""A transfer ANAF knows about stays in Odoo until ANAF is told otherwise.

Once a UIT is issued, the transfer is the record behind a declaration: it
cannot be deleted or cancelled while the notification is alive, and the data
it was declared with cannot change while ANAF is still processing it. The
deletion (DEL), confirmation (CON) and vehicle change (MVH) are only sent on
a notification ANAF validated. ANAF itself is mocked.
"""

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..models.l10n_ro_edi_stock_document import _document_state_ondelete

_REQUEST = (
    "odoo.addons.l10n_ro_edi_stock.models.etransport_api.ETransportAPI."
    "_make_etransport_request"
)


def _anaf_answering(stare="ok", errors=None):
    """A mocked ANAF: uploads get a load index, status calls get ``stare``."""

    def answer(company, endpoint, method, session=None, data=None):
        if endpoint.startswith("stareMesaj"):
            content = {"stare": stare}
            if errors:
                content["Errors"] = [{"errorMessage": error} for error in errors]
            return {"content": content}
        return {"content": {"index_incarcare": "42", "UIT": "UIT0000000000001"}}

    return answer


_anaf = _anaf_answering()


class EtransportIntegrityCommon(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write(
            {
                "account_fiscal_country_id": cls.env.ref("base.ro").id,
                "vat": "RO1234567897",
                "l10n_ro_edi_access_token": "token",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "Client", "country_id": cls.env.ref("base.ro").id}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Marfa", "is_storable": True, "list_price": 100.0}
        )
        cls.outgoing_type = cls.env["stock.picking.type"].search(
            [("code", "=", "outgoing"), ("company_id", "=", cls.company.id)], limit=1
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Transportator",
                "product_id": cls.env["product.product"]
                .create({"name": "Transport", "type": "service"})
                .id,
                "l10n_ro_edi_stock_partner_id": cls.partner.id,
            }
        )

    def _picking(self):
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "carrier_id": self.carrier.id,
                "picking_type_id": self.outgoing_type.id,
                "location_id": self.outgoing_type.default_location_src_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "move_ids": [
                    (0, 0, {"product_id": self.product.id, "product_uom_qty": 5})
                ],
            }
        )
        picking.action_confirm()
        return picking

    def _send(self, record, uit="UIT0000000000001"):
        """What the base module stores when ANAF accepts the upload."""
        record._l10n_ro_edi_stock_create_document_stock_sent(
            {
                "l10n_ro_edi_stock_load_id": "41",
                "l10n_ro_edi_stock_uit": uit,
                "raw_xml": "<eTransport/>",
            }
        )
        self.assertEqual(record.l10n_ro_edi_stock_state, "stock_sent")
        return record

    def _validate(self, record):
        self._send(record)
        with patch(_REQUEST, side_effect=_anaf):
            record.action_l10n_ro_edi_stock_fetch_status()
        self.assertEqual(record.l10n_ro_edi_stock_state, "stock_validated")
        return record

    def _wizard(self, record, action_type, answer="ok", **vals):
        """Send the action, then fetch ANAF's answer to it (``answer=None``
        leaves it waiting)."""
        wizard = (
            self.env["l10n.ro.edi.stock.action.wizard"]
            .with_context(active_id=record.id, active_model=record._name)
            .create({"action_type": action_type, **vals})
        )
        with patch(_REQUEST, side_effect=_anaf):
            result = wizard.action_execute()
        self.assertEqual(record.l10n_ro_edi_stock_state, "stock_action_sent")
        if answer:
            self._fetch(record, answer)
        return result

    def _fetch(self, record, answer="ok", errors=None):
        with patch(_REQUEST, side_effect=_anaf_answering(answer, errors)):
            record.action_l10n_ro_edi_stock_fetch_status()


@tagged("post_install", "-at_install")
class TestEtransportPickingIntegrity(EtransportIntegrityCommon):
    # ------------------------------------------------------------------
    # Fara UIT, transferul e liber
    # ------------------------------------------------------------------
    def test_a_transfer_never_notified_can_be_cancelled_and_deleted(self):
        picking = self._picking()
        picking.action_cancel()
        self.assertEqual(picking.state, "cancel")
        picking.unlink()
        self.assertFalse(picking.exists())

    def test_a_failed_first_notification_does_not_hold_the_transfer(self):
        picking = self._picking()
        picking._l10n_ro_edi_stock_create_document_stock_sending_failed(
            {"message": "Lipseste codul tarifar"}
        )
        picking.action_cancel()
        self.assertEqual(picking.state, "cancel")

    # ------------------------------------------------------------------
    # UIT trimis, in prelucrare la ANAF
    # ------------------------------------------------------------------
    def test_a_transfer_being_processed_cannot_be_cancelled_or_deleted(self):
        picking = self._send(self._picking())
        with self.assertRaises(UserError):
            picking.action_cancel()
        with self.assertRaises(UserError):
            picking.unlink()
        self.assertEqual(picking.state, "confirmed")

    def test_the_declared_data_is_frozen_while_anaf_processes_it(self):
        picking = self._send(self._picking())
        with self.assertRaises(UserError):
            picking.l10n_ro_edi_stock_vehicle_number = "TM99XYZ"
        with self.assertRaises(UserError):
            picking.l10n_ro_edi_stock_price_source = "list"
        with self.assertRaises(UserError):
            self.env["l10n.ro.edi.stock.document.line"].create(
                {"picking_id": picking.id, "document_date": "2026-11-05"}
            )
        with self.assertRaises(UserError):
            self.env["l10n.ro.edi.stock.previous.notification"].create(
                {"picking_id": picking.id, "uit": "UIT0000000000009"}
            )
        self.assertFalse(picking.l10n_ro_edi_stock_vehicle_number)
        self.assertEqual(picking.l10n_ro_edi_stock_price_source, "auto")

    def test_the_document_lines_already_declared_are_frozen_too(self):
        picking = self._picking()
        line = self.env["l10n.ro.edi.stock.document.line"].create(
            {"picking_id": picking.id, "document_date": "2026-11-05"}
        )
        line.document_number = "FCT-1"
        self._send(picking)
        with self.assertRaises(UserError):
            line.document_number = "FCT-2"
        with self.assertRaises(UserError):
            line.unlink()
        self.assertEqual(line.document_number, "FCT-1")

    def test_the_rest_of_the_transfer_stays_editable_while_processing(self):
        picking = self._send(self._picking())
        picking.note = "Livrare dupa ora 10"
        picking.message_post(body="Sunat clientul")
        self.assertEqual(str(picking.note), "<p>Livrare dupa ora 10</p>")

    def test_no_deletion_can_be_sent_while_anaf_still_processes(self):
        picking = self._send(self._picking())
        with self.assertRaises(UserError):
            self._wizard(picking, "delete")
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_sent")

    # ------------------------------------------------------------------
    # UIT validat
    # ------------------------------------------------------------------
    def test_flow_validated_uit_holds_the_transfer_until_deleted(self):
        picking = self._validate(self._picking())
        with self.assertRaises(UserError):
            picking.action_cancel()
        with self.assertRaises(UserError):
            picking.unlink()
        # editable again once ANAF answered
        picking.l10n_ro_edi_stock_remarks = "Observatie"
        self._wizard(picking, "delete")
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_deleted")
        deletion = picking.l10n_ro_edi_stock_document_ids.sorted()[0]
        self.assertEqual(deletion.l10n_ro_edi_stock_event_type, "DEL")
        self.assertEqual(deletion.l10n_ro_edi_stock_uit, "UIT0000000000001")
        picking.action_cancel()
        self.assertEqual(picking.state, "cancel")
        picking.unlink()
        self.assertFalse(picking.exists())

    def test_flow_a_confirmed_transport_holds_the_transfer_for_good(self):
        picking = self._validate(self._picking())
        self._wizard(picking, "confirm", confirmation_type="10")
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_confirmed")
        with self.assertRaises(UserError):
            picking.action_cancel()
        with self.assertRaises(UserError):
            self._wizard(picking, "delete")

    def test_flow_after_a_vehicle_change_delete_confirm_and_amend_stay_open(self):
        picking = self._validate(self._picking())
        self._wizard(picking, "modify_vehicle", new_vehicle_number="tm01abc")
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_vehicle_modified")
        self.assertEqual(picking.l10n_ro_edi_stock_vehicle_number, "tm01abc")
        self.assertTrue(picking.l10n_ro_edi_stock_enable_amend)
        with self.assertRaises(UserError):
            picking.action_cancel()
        self._wizard(picking, "delete")
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_deleted")
        picking.action_cancel()
        self.assertEqual(picking.state, "cancel")

    def test_a_confirmation_needs_a_validated_notification(self):
        picking = self._picking()
        with self.assertRaises(UserError):
            self._wizard(picking, "confirm", confirmation_type="10", uit="X")
        self._send(picking)
        with self.assertRaises(UserError):
            self._wizard(picking, "confirm", confirmation_type="10")
        with self.assertRaises(UserError):
            self._wizard(picking, "modify_vehicle", new_vehicle_number="TM01ABC")
        self.assertEqual(len(picking.l10n_ro_edi_stock_document_ids), 1)

    def test_a_failed_correction_keeps_the_uit_alive(self):
        """ANAF still holds the validated notification."""
        picking = self._validate(self._picking())
        picking._l10n_ro_edi_stock_create_document_stock_sending_failed(
            {
                "message": "Corectie respinsa",
                "l10n_ro_edi_stock_uit": "UIT0000000000001",
            }
        )
        with self.assertRaises(UserError):
            picking.action_cancel()
        self._wizard(picking, "delete")
        picking.action_cancel()
        self.assertEqual(picking.state, "cancel")

    def test_the_action_is_sent_only_for_the_current_uit(self):
        picking = self._validate(self._picking())
        with self.assertRaises(UserError):
            self._wizard(picking, "delete", uit="UIT0000000000099")
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_validated")

    # ------------------------------------------------------------------
    # Raspunsul ANAF la stergere / confirmare / schimbare vehicul
    # ------------------------------------------------------------------
    def test_a_deletion_waiting_for_anaf_still_holds_the_transfer(self):
        picking = self._validate(self._picking())
        self._wizard(picking, "delete", answer=None)
        self.assertTrue(picking.l10n_ro_edi_stock_enable_fetch)
        self.assertFalse(picking.l10n_ro_edi_stock_enable_uit_action)
        with self.assertRaises(UserError):
            picking.action_cancel()
        with self.assertRaises(UserError):
            picking.unlink()
        with self.assertRaises(UserError):
            self._wizard(picking, "confirm", confirmation_type="10")
        self._fetch(picking, "in prelucrare")
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_action_sent")
        self._fetch(picking, "ok")
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_deleted")
        picking.action_cancel()
        self.assertEqual(picking.state, "cancel")

    def test_a_refused_deletion_leaves_the_uit_live(self):
        picking = self._validate(self._picking())
        self._wizard(picking, "delete", answer="nok")
        document = picking.l10n_ro_edi_stock_document_ids.sorted()[0]
        self.assertEqual(document.state, "stock_sending_failed")
        self.assertEqual(document.l10n_ro_edi_stock_event_type, "DEL")
        self.assertIn("nok", document.message)
        with self.assertRaises(UserError):
            picking.action_cancel()
        # the validated notification is still there: the deletion can be retried
        self.assertTrue(picking.l10n_ro_edi_stock_enable_uit_action)
        self._wizard(picking, "delete")
        picking.action_cancel()
        self.assertEqual(picking.state, "cancel")

    def test_anaf_error_details_are_kept_on_the_document(self):
        picking = self._validate(self._picking())
        self._wizard(picking, "confirm", answer=None, confirmation_type="10")
        self._fetch(picking, "XML cu erori nepreluat de sistem", ["UIT inexistent"])
        document = picking.l10n_ro_edi_stock_document_ids.sorted()[0]
        self.assertEqual(document.state, "stock_sending_failed")
        self.assertIn("UIT inexistent", document.message)
        self.assertTrue(picking.l10n_ro_edi_stock_enable_uit_action)

    def test_an_unreachable_anaf_leaves_the_action_waiting(self):
        picking = self._validate(self._picking())
        self._wizard(picking, "delete", answer=None)
        with patch(_REQUEST, return_value={"error": "timeout"}):
            picking.action_l10n_ro_edi_stock_fetch_status()
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_action_sent")

    def test_a_confirmation_accepted_and_refused(self):
        picking = self._validate(self._picking())
        self._wizard(picking, "confirm", answer="nok", confirmation_type="10")
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_sending_failed")
        self._wizard(picking, "confirm", confirmation_type="20")
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_confirmed")
        confirmation = picking.l10n_ro_edi_stock_document_ids.sorted()[0]
        self.assertEqual(confirmation.l10n_ro_edi_stock_confirm_type, "20")

    def test_the_vehicle_changes_only_once_anaf_accepts_it(self):
        picking = self._validate(self._picking())
        picking.l10n_ro_edi_stock_vehicle_number = "TM00OLD"
        self._wizard(
            picking,
            "modify_vehicle",
            answer=None,
            new_vehicle_number="TM01NEW",
            trailer_1_number="TM02REM",
        )
        self.assertEqual(picking.l10n_ro_edi_stock_vehicle_number, "TM00OLD")
        self._fetch(picking, "nok")
        self.assertEqual(picking.l10n_ro_edi_stock_vehicle_number, "TM00OLD")
        self.assertTrue(picking.l10n_ro_edi_stock_enable_uit_action)
        self._wizard(
            picking,
            "modify_vehicle",
            new_vehicle_number="TM01NEW",
            trailer_1_number="TM02REM",
        )
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_vehicle_modified")
        self.assertEqual(picking.l10n_ro_edi_stock_vehicle_number, "TM01NEW")
        self.assertEqual(picking.l10n_ro_edi_stock_trailer_1_number, "TM02REM")

    def test_the_cron_fetches_waiting_actions(self):
        picking = self._validate(self._picking())
        self._wizard(picking, "delete", answer=None)
        with patch(_REQUEST, side_effect=_anaf):
            self.env["stock.picking"]._l10n_ro_edi_stock_cron_fetch_status()
        self.assertEqual(picking.l10n_ro_edi_stock_state, "stock_deleted")

    # ------------------------------------------------------------------
    # Dezinstalarea pastreaza urma trimisa la ANAF
    # ------------------------------------------------------------------
    def test_uninstalling_keeps_the_action_documents(self):
        picking = self._validate(self._picking())
        self._wizard(picking, "modify_vehicle", new_vehicle_number="TM01NEW")
        self._wizard(picking, "delete")
        deletion, change = picking.l10n_ro_edi_stock_document_ids.sorted()[:2]
        _document_state_ondelete("stock_deleted")(deletion)
        self.assertEqual(deletion.state, "stock_sending_failed")
        self.assertIn("stock_deleted / DEL", deletion.message)
        self.assertEqual(
            _document_state_ondelete("stock_vehicle_modified"),
            "set stock_validated",
        )
        self.assertTrue(change.exists())
