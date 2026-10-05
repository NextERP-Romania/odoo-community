# Copyright 2026 NextERP Romania
# License LGPL-3
"""Catalog of CIUS-RO (UBL 2.1) nodes that may be filled differently per partner.

Odoo ships a similar catalog for Peppol in
``account_edi_ubl_cii/tools/ubl_20_optional_fields.py``
(``PEPPOL_COMMON_OPTIONAL_FIELDS``), but there the link between a node and its
value is hardcoded on a Studio field of ``account.move``, identical for every
customer. Here the catalog only declares *which* nodes may be written; *what*
goes in them is configured per partner (see ``l10n_ro.edi.xml.rule``).

Each entry declares:

``label``      human readable name shown in the selection field, prefixed with
               the EN 16931 business term;
``scope``      ``document`` for nodes on the Invoice/CreditNote root,
               ``line`` for nodes on an InvoiceLine/CreditNoteLine;
``path``       tuple of UBL tags, relative to that root;
``attribute``  name of the XML attribute to write instead of the node text,
               when the business term is carried by an attribute;
``max_len``    CIUS-RO schematron limit (BR-RO-Lxxx), enforced on the value;
``doc_types``  the document types the node exists on, when UBL does not define
               it on both (e.g. a credit note has no ProjectReference);
``help``       short explanation of what ANAF expects in the node.

Every path here is checked against Odoo's own UBL templates
(``account_edi_ubl_cii/tools/ubl_21_invoice.py`` and ``ubl_21_credit_note.py``)
by ``tests/test_ciusro_fields.py``: ``dict_to_xml`` raises a ``ValueError`` on
any tag missing from the template, so an invalid path here would break the
export instead of degrading gracefully.
"""

CUSTOM_KEY = "custom"

CIUSRO_FIELDS = {
    # -- Document level: references ---------------------------------------
    "buyer_reference": {
        "label": "BT-10 Buyer reference",
        "scope": "document",
        "path": ("cbc:BuyerReference",),
        "max_len": 200,
        "help": "Identifier assigned by the buyer, often its internal "
        "accounting or cost centre code. Several retailers reject "
        "invoices that do not carry it.",
    },
    "project_reference": {
        "label": "BT-11 Project reference",
        "scope": "document",
        "path": ("cac:ProjectReference", "cbc:ID"),
        "doc_types": ("invoice",),
        "max_len": 200,
        "help": "Identifier of the project the invoice relates to.",
    },
    "contract_reference": {
        "label": "BT-12 Contract reference",
        "scope": "document",
        "path": ("cac:ContractDocumentReference", "cbc:ID"),
        "max_len": 200,
        "help": "Number of the contract between the two parties.",
    },
    "order_reference": {
        "label": "BT-13 Purchase order reference",
        "scope": "document",
        "path": ("cac:OrderReference", "cbc:ID"),
        "max_len": 200,
        "help": "The buyer's purchase order number. Odoo falls back to the "
        "invoice 'Customer Reference' or its own name, which most "
        "retail buyers refuse to reconcile against.",
    },
    "sales_order_reference": {
        "label": "BT-14 Sales order reference",
        "scope": "document",
        "path": ("cac:OrderReference", "cbc:SalesOrderID"),
        "max_len": 200,
        "help": "The seller's own sales order number.",
    },
    "despatch_reference": {
        "label": "BT-16 Despatch advice reference",
        "scope": "document",
        "path": ("cac:DespatchDocumentReference", "cbc:ID"),
        "max_len": 200,
        "help": "Number of the delivery note / despatch advice the invoice settles.",
    },
    "originator_reference": {
        "label": "BT-17 Tender or lot reference",
        "scope": "document",
        "path": ("cac:OriginatorDocumentReference", "cbc:ID"),
        "max_len": 200,
        "help": "Tender or lot number, required by most public buyers.",
    },
    "accounting_cost": {
        "label": "BT-19 Buyer accounting reference",
        "scope": "document",
        "path": ("cbc:AccountingCost",),
        "max_len": 100,
        "help": "Accounting code assigned by the buyer, used to route the "
        "invoice to the right cost centre on their side.",
    },
    "tax_point_date": {
        "label": "BT-7 Value added tax point date",
        "scope": "document",
        "path": ("cbc:TaxPointDate",),
        "help": "Date on which VAT becomes chargeable, when it differs from "
        "the invoice date.",
    },
    "period_start": {
        "label": "BT-73 Invoicing period start date",
        "scope": "document",
        "path": ("cac:InvoicePeriod", "cbc:StartDate"),
        "help": "First day of the period the invoice covers.",
    },
    "period_end": {
        "label": "BT-74 Invoicing period end date",
        "scope": "document",
        "path": ("cac:InvoicePeriod", "cbc:EndDate"),
        "help": "Last day of the period the invoice covers.",
    },
    "note": {
        "label": "BT-22 Invoice note",
        "scope": "document",
        "path": ("cbc:Note",),
        "max_len": 300,
        "help": "Free text note. CIUS-RO caps each note at 300 characters.",
    },
    # -- Document level: parties ------------------------------------------
    "supplier_endpoint": {
        "label": "BT-34 Seller electronic address",
        "scope": "document",
        "path": ("cac:AccountingSupplierParty", "cac:Party", "cbc:EndpointID"),
        "help": "Electronic address of the seller, e.g. its GLN.",
    },
    "supplier_endpoint_scheme": {
        "label": "BT-34-1 Seller electronic address scheme",
        "scope": "document",
        "path": ("cac:AccountingSupplierParty", "cac:Party", "cbc:EndpointID"),
        "attribute": "schemeID",
        "help": "Scheme of the seller electronic address, e.g. 0088 for a GLN.",
    },
    "supplier_party_identification": {
        "label": "BT-29 Seller identifier",
        "scope": "document",
        "path": (
            "cac:AccountingSupplierParty",
            "cac:Party",
            "cac:PartyIdentification",
            "cbc:ID",
        ),
        "max_len": 200,
        "help": "Identifier of the seller in the buyer's own systems, e.g. the "
        "vendor code the retailer assigned us.",
    },
    "customer_endpoint": {
        "label": "BT-49 Buyer electronic address",
        "scope": "document",
        "path": ("cac:AccountingCustomerParty", "cac:Party", "cbc:EndpointID"),
        "help": "Electronic address of the buyer, e.g. its GLN.",
    },
    "customer_endpoint_scheme": {
        "label": "BT-49-1 Buyer electronic address scheme",
        "scope": "document",
        "path": ("cac:AccountingCustomerParty", "cac:Party", "cbc:EndpointID"),
        "attribute": "schemeID",
        "help": "Scheme of the buyer electronic address, e.g. 0088 for a GLN.",
    },
    "customer_party_identification": {
        "label": "BT-46 Buyer identifier",
        "scope": "document",
        "path": (
            "cac:AccountingCustomerParty",
            "cac:Party",
            "cac:PartyIdentification",
            "cbc:ID",
        ),
        "max_len": 200,
        "help": "Identifier of the buyer, e.g. its GLN or the store number.",
    },
    # -- Document level: delivery and payment ------------------------------
    "actual_delivery_date": {
        "label": "BT-72 Actual delivery date",
        "scope": "document",
        "path": ("cac:Delivery", "cbc:ActualDeliveryDate"),
        "help": "Date the goods were actually delivered.",
    },
    "delivery_location_id": {
        "label": "BT-71 Deliver to location identifier",
        "scope": "document",
        "path": ("cac:Delivery", "cac:DeliveryLocation", "cbc:ID"),
        "max_len": 200,
        "help": "Identifier of the delivery point, e.g. the GLN of the store "
        "or warehouse that received the goods.",
    },
    "delivery_location_scheme": {
        "label": "BT-71-1 Deliver to location scheme",
        "scope": "document",
        "path": ("cac:Delivery", "cac:DeliveryLocation", "cbc:ID"),
        "attribute": "schemeID",
        "help": "Scheme of the delivery point identifier, e.g. 0088 for a GLN.",
    },
    "delivery_party_name": {
        "label": "BT-70 Deliver to party name",
        "scope": "document",
        "path": ("cac:Delivery", "cac:DeliveryParty", "cac:PartyName", "cbc:Name"),
        "max_len": 200,
        "help": "Name of the party the goods were delivered to.",
    },
    "payment_id": {
        "label": "BT-83 Remittance information",
        "scope": "document",
        "path": ("cac:PaymentMeans", "cbc:PaymentID"),
        "max_len": 140,
        "help": "Reference the buyer must quote on the payment, e.g. a "
        "structured remittance reference.",
    },
    "payment_terms_note": {
        "label": "BT-20 Payment terms",
        "scope": "document",
        "path": ("cac:PaymentTerms", "cbc:Note"),
        "max_len": 300,
        "help": "Text describing the payment terms.",
    },
    # -- Line level --------------------------------------------------------
    "line_order_line_reference": {
        "label": "BT-132 Referenced purchase order line",
        "scope": "line",
        "path": ("cac:OrderLineReference", "cbc:LineID"),
        "max_len": 200,
        "help": "Line number of the buyer's purchase order this line settles. "
        "Retailers match invoice lines to order lines on it.",
    },
    "line_note": {
        "label": "BT-127 Invoice line note",
        "scope": "line",
        "path": ("cbc:Note",),
        "max_len": 300,
        "help": "Free text note on the line.",
    },
    "line_item_name": {
        "label": "BT-153 Item name",
        "scope": "line",
        "path": ("cac:Item", "cbc:Name"),
        "max_len": 100,
        "help": "Overrides the product name sent to this partner.",
    },
    "line_item_description": {
        "label": "BT-154 Item description",
        "scope": "line",
        "path": ("cac:Item", "cbc:Description"),
        "max_len": 200,
        "help": "Overrides the product description sent to this partner.",
    },
    "line_sellers_item_id": {
        "label": "BT-155 Item seller's identifier",
        "scope": "line",
        "path": ("cac:Item", "cac:SellersItemIdentification", "cbc:ID"),
        "max_len": 200,
        "help": "Our own article number for the product.",
    },
    "line_buyers_item_id": {
        "label": "BT-156 Item buyer's identifier",
        "scope": "line",
        "path": ("cac:Item", "cac:BuyersItemIdentification", "cbc:ID"),
        "max_len": 200,
        "help": "The article number the buyer uses for the product. Odoo never "
        "fills it, since it only knows our own references.",
    },
    "line_standard_item_id": {
        "label": "BT-157 Item standard identifier",
        "scope": "line",
        "path": ("cac:Item", "cac:StandardItemIdentification", "cbc:ID"),
        "max_len": 200,
        "help": "Standard identifier of the product, typically its EAN/GTIN.",
    },
    "line_standard_item_scheme": {
        "label": "BT-157-1 Item standard identifier scheme",
        "scope": "line",
        "path": ("cac:Item", "cac:StandardItemIdentification", "cbc:ID"),
        "attribute": "schemeID",
        "help": "Scheme of the standard identifier, e.g. 0160 for a GTIN.",
    },
    "line_document_reference": {
        "label": "BT-128 Invoice line object identifier",
        "scope": "line",
        "path": ("cac:DocumentReference", "cbc:ID"),
        "max_len": 200,
        "help": "Identifier of an object this line refers to, e.g. a meter or "
        "a subscription number.",
    },
}


def get_field(key):
    """Return the catalog entry for ``key``, or an empty dict for a custom path."""
    return CIUSRO_FIELDS.get(key) or {}


def get_selection(scope=None):
    """Return the ``(key, label)`` pairs to offer in the UI."""
    return [
        (key, entry["label"])
        for key, entry in CIUSRO_FIELDS.items()
        if scope is None or entry["scope"] == scope
    ]
