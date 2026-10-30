from odoo import models
from odoo.tools import html2plaintext

# CIUS-RO maximum character lengths enforced by the ANAF SPV schematron
# (rules BR-RO-L020 .. BR-RO-L1000). Values are Unicode character counts
# matching the XPath ``string-length`` semantics used by the validator.

_DOCUMENT_LIMITS = {
    ("cbc:ID",): 200,  # BT-1
    ("cac:ContractDocumentReference", "cbc:ID"): 200,  # BT-12
    ("cac:OrderReference", "cbc:ID"): 200,  # BT-13
    ("cac:OrderReference", "cbc:SalesOrderID"): 200,  # BT-14
    ("cac:ReceiptDocumentReference", "cbc:ID"): 200,  # BT-15
    ("cac:DespatchDocumentReference", "cbc:ID"): 200,  # BT-16
    ("cac:OriginatorDocumentReference", "cbc:ID"): 200,  # BT-17
    ("cbc:AccountingCost",): 100,  # BT-19
    ("cac:PaymentTerms", "cbc:Note"): 300,  # BT-20
}

_PARTY_PATHS = {
    ("cac:Party", "cac:PartyLegalEntity", "cbc:RegistrationName"): 200,  # BT-27/44
    ("cac:Party", "cac:PartyName", "cbc:Name"): 200,  # BT-28/45
    ("cac:Party", "cac:PartyLegalEntity", "cbc:CompanyLegalForm"): 1000,  # BT-33
    ("cac:Party", "cac:PostalAddress", "cbc:StreetName"): 150,  # BT-35/50/64
    ("cac:Party", "cac:PostalAddress", "cbc:AdditionalStreetName"): 100,  # BT-36/51/65
    ("cac:Party", "cac:PostalAddress", "cbc:CityName"): 50,  # BT-37/52/66
    ("cac:Party", "cac:PostalAddress", "cbc:PostalZone"): 20,  # BT-38/53/67
    ("cac:Party", "cac:Contact", "cbc:Name"): 100,  # BT-41/56
    ("cac:Party", "cac:Contact", "cbc:Telephone"): 100,  # BT-42/57
    ("cac:Party", "cac:Contact", "cbc:ElectronicMail"): 100,  # BT-43/58
}

_DELIVERY_PATHS = {
    ("cac:DeliveryParty", "cac:PartyName", "cbc:Name"): 200,  # BT-70
    ("cac:DeliveryLocation", "cac:Address", "cbc:StreetName"): 150,  # BT-75
    ("cac:DeliveryLocation", "cac:Address", "cbc:AdditionalStreetName"): 100,  # BT-76
    ("cac:DeliveryLocation", "cac:Address", "cbc:CityName"): 50,  # BT-77
    ("cac:DeliveryLocation", "cac:Address", "cbc:PostalZone"): 20,  # BT-78
}

_PAYMENT_MEANS_PATHS = {
    ("cbc:PaymentMeansCode", "name"): 100,  # BT-82 (attribute)
    ("cbc:PaymentID",): 140,  # BT-83
    ("cac:PayeeFinancialAccount", "cbc:Name"): 200,  # BT-85
    ("cac:CardAccount", "cbc:HolderName"): 200,  # BT-88
}

_DOC_ALLOWANCE_PATHS = {
    ("cbc:AllowanceChargeReason",): 100,  # BT-97 / BT-104
}

_ADDITIONAL_DOC_REF_PATHS = {
    ("cbc:ID",): 200,  # BT-18 / BT-122
    ("cbc:DocumentDescription",): 100,  # BT-123
    ("cac:Attachment", "cac:ExternalReference", "cbc:URI"): 200,  # BT-124
    ("cac:Attachment", "cbc:EmbeddedDocumentBinaryObject", "filename"): 200,  # BT-125-2
}

_BILLING_REF_PATHS = {
    ("cac:InvoiceDocumentReference", "cbc:ID"): 200,  # BT-25
}

_LINE_PATHS = {
    ("cbc:AccountingCost",): 100,  # BT-133
    ("cac:AllowanceCharge", "cbc:AllowanceChargeReason"): 100,  # BT-139 / BT-144
    ("cac:Item", "cbc:Name"): 100,  # BT-153
    ("cac:Item", "cbc:Description"): 200,  # BT-154
}

_ITEM_ADDITIONAL_PROPERTY_PATHS = {
    ("cbc:Name",): 50,  # BT-160
    ("cbc:Value",): 100,  # BT-161
}

# BT-22 / BT-127 (header / line cbc:Note) are not truncated — they are
# split into multiple cbc:Note tags of at most 300 chars each, because
# UBL allows the element to repeat.
_NOTE_MAX_LEN = 300


class AccountEdiXmlUBLRO(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_ro"

    # ------------------------------------------------------------------
    # String helpers
    # ------------------------------------------------------------------

    def _ro_truncate(self, value, max_len):
        if not value:
            return value
        return str(value)[:max_len]

    def split_string(self, string, max_len=_NOTE_MAX_LEN):
        # Cap each chunk at ``max_len`` Unicode chars *and* ``max_len``
        # UTF-8 bytes — the schematron counts characters, but byte-based
        # validators have been seen in the wild and diacritics double in
        # UTF-8, so we stay below both ceilings.
        result = []
        while string:
            chunk = string[:max_len]
            while len(chunk.encode("utf-8")) > max_len:
                chunk = chunk[:-1]
            chunk = chunk.strip()
            if chunk:
                result.append(chunk)
            string = string[len(chunk) :].lstrip()
        return result

    def _ro_truncate_text(self, node, max_len):
        if isinstance(node, dict) and node.get("_text"):
            node["_text"] = self._ro_truncate(node["_text"], max_len)

    def _ro_apply_path(self, root, path, max_len):
        """Walk ``path`` from ``root`` truncating the leaf value.

        Intermediate nodes that are lists are iterated. The leaf may be a
        text node (``{'_text': ...}``) or an XML attribute (the path then
        ends with the attribute name and the parent holds it as a string).
        """

        def _walk(node, remaining):
            if node is None:
                return
            if isinstance(node, list):
                for item in node:
                    _walk(item, remaining)
                return
            if not remaining:
                self._ro_truncate_text(node, max_len)
                return
            head, *rest = remaining
            if not isinstance(node, dict):
                return
            child = node.get(head)
            if child is None:
                return
            if not rest and isinstance(child, str):
                node[head] = self._ro_truncate(child, max_len)
                return
            _walk(child, rest)

        _walk(root, list(path))

    @staticmethod
    def _ro_iter_children(parent, key):
        if not isinstance(parent, dict):
            return
        value = parent.get(key)
        if value is None:
            return
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
        elif isinstance(value, dict):
            yield value

    # ------------------------------------------------------------------
    # Header / line builders
    # ------------------------------------------------------------------

    def _add_invoice_header_nodes(self, document_node, vals):
        res = super()._add_invoice_header_nodes(document_node, vals)

        # BT-22 — split the invoice note into repeated cbc:Note tags
        # (max 300 chars each, BR-RO-L300).
        invoice = vals["invoice"]
        if invoice.narration:
            plain = html2plaintext(invoice.narration).strip()
            if plain:
                document_node["cbc:Note"] = [
                    {"_text": s} for s in self.split_string(plain, _NOTE_MAX_LEN)
                ]
        return res

    def _add_invoice_line_note_nodes(self, line_node, vals):
        # BT-127 — split the invoice line note into repeated cbc:Note
        # tags (max 300 chars each, BR-RO-L300).
        super()._add_invoice_line_note_nodes(line_node, vals)
        note = line_node.get("cbc:Note")
        text = (
            note.get("_text")
            if isinstance(note, dict)
            else (note if isinstance(note, str) else None)
        )
        if not text:
            return
        line_node["cbc:Note"] = [
            {"_text": s} for s in self.split_string(text, _NOTE_MAX_LEN)
        ]

    def _ubl_add_line_item_name_description_nodes(self, vals):
        item_node = vals["item_node"]
        base_line = vals["line_vals"]["base_line"]
        product = base_line["product_id"]

        if base_line.get("_removed_tax_data"):
            name = description = base_line["_removed_tax_data"]["tax"].name
        else:
            name = product.name or ""
            if line_name := base_line.get("name"):
                description = line_name
                if not name:
                    name = line_name
            else:
                description = product.description_sale or ""

        # BT-154 — Item description, max 200 chars (BR-RO-L200).
        if description:
            item_node["cbc:Description"] = {
                "_text": self._ro_truncate(description, 200)
            }
        else:
            item_node["cbc:Description"] = None

        # BT-153 — Item name, max 100 chars (BR-RO-L100).
        if name:
            item_node["cbc:Name"] = {"_text": self._ro_truncate(name, 100)}
        else:
            item_node["cbc:Name"] = None

    # ------------------------------------------------------------------
    # Final pass: enforce all BR-RO-L* length limits in one walk
    # ------------------------------------------------------------------

    def _get_invoice_node(self, vals):
        document_node = super()._get_invoice_node(vals)
        self._ro_apply_length_limits(document_node)
        return document_node

    def _ro_apply_length_limits(self, document_node):
        for path, max_len in _DOCUMENT_LIMITS.items():
            self._ro_apply_path(document_node, path, max_len)

        for party_key in (
            "cac:AccountingSupplierParty",
            "cac:AccountingCustomerParty",
            "cac:PayeeParty",
            "cac:TaxRepresentativeParty",
        ):
            party_root = document_node.get(party_key)
            if party_root is None:
                continue
            for path, max_len in _PARTY_PATHS.items():
                self._ro_apply_path(party_root, path, max_len)

        delivery_root = document_node.get("cac:Delivery")
        if delivery_root is not None:
            for path, max_len in _DELIVERY_PATHS.items():
                self._ro_apply_path(delivery_root, path, max_len)

        for pm in self._ro_iter_children(document_node, "cac:PaymentMeans"):
            for path, max_len in _PAYMENT_MEANS_PATHS.items():
                self._ro_apply_path(pm, path, max_len)

        for ac in self._ro_iter_children(document_node, "cac:AllowanceCharge"):
            for path, max_len in _DOC_ALLOWANCE_PATHS.items():
                self._ro_apply_path(ac, path, max_len)

        # BT-120 — VAT exemption reason inside each TaxCategory.
        for tt in self._ro_iter_children(document_node, "cac:TaxTotal"):
            for sub in self._ro_iter_children(tt, "cac:TaxSubtotal"):
                cat = sub.get("cac:TaxCategory")
                if isinstance(cat, dict):
                    self._ro_truncate_text(cat.get("cbc:TaxExemptionReason"), 100)

        for adr in self._ro_iter_children(
            document_node, "cac:AdditionalDocumentReference"
        ):
            for path, max_len in _ADDITIONAL_DOC_REF_PATHS.items():
                self._ro_apply_path(adr, path, max_len)

        for br in self._ro_iter_children(document_node, "cac:BillingReference"):
            for path, max_len in _BILLING_REF_PATHS.items():
                self._ro_apply_path(br, path, max_len)

        for line_tag in ("cac:InvoiceLine", "cac:CreditNoteLine", "cac:DebitNoteLine"):
            for line in self._ro_iter_children(document_node, line_tag):
                for path, max_len in _LINE_PATHS.items():
                    self._ro_apply_path(line, path, max_len)
                item = line.get("cac:Item")
                if isinstance(item, dict):
                    for prop in self._ro_iter_children(
                        item, "cac:AdditionalItemProperty"
                    ):
                        for path, max_len in _ITEM_ADDITIONAL_PROPERTY_PATHS.items():
                            self._ro_apply_path(prop, path, max_len)
