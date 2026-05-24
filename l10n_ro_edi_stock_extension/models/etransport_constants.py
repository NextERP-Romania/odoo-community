# Copyright 2026 NextERP Romania SRL
# Constants derived from XSD v2 + Schematron v2.0.2 (ANAF eTransport)

INCOMING_OPERATIONS = ("10", "12", "14", "40", "60")
OUTGOING_OPERATIONS = ("20", "22", "24", "50", "70")
NATIONAL_OPERATIONS = ("30",)
NO_GOODS_DATA_OPERATIONS = ("60", "70")

DOCUMENT_TYPES = [
    ("10", "CMR"),
    ("20", "Invoice"),
    ("30", "Delivery slip"),
    ("9999", "Other"),
]

CONFIRMATION_TYPES = [
    ("10", "Confirmed"),
    ("20", "Partially confirmed"),
    ("30", "Refused"),
]

EU_COUNTRY_CODES = {
    "AT",
    "BE",
    "BG",
    "CZ",
    "CY",
    "DE",
    "DK",
    "EE",
    "EL",
    "ES",
    "FI",
    "HR",
    "HU",
    "IE",
    "IT",
    "FR",
    "LV",
    "LT",
    "LU",
    "MT",
    "NL",
    "PL",
    "PT",
    "RO",
    "SI",
    "SE",
    "SK",
    "XI",
}

VALID_COUNTRY_CODE_MAP = {
    "GR": "EL",
}

OPERATION_TYPE_TO_ALLOWED_SCOPE_CODES_FULL = {
    "10": (
        "101",
        "201",
        "301",
        "401",
        "501",
        "601",
        "703",
        "801",
        "802",
        "901",
        "1001",
        "1101",
        "9901",
    ),
    "12": ("9999",),
    "14": ("9999",),
    "20": ("101", "301", "703", "801", "802", "9901"),
    "22": ("9999",),
    "24": ("9999",),
    "30": ("101", "704", "705", "9901"),
    "40": ("9999",),
    "50": ("9999",),
    "60": ("9999",),
    "70": ("9999",),
}


def is_incoming(operation_type):
    return operation_type in INCOMING_OPERATIONS


def is_outgoing(operation_type):
    return operation_type in OUTGOING_OPERATIONS


def is_national(operation_type):
    return operation_type in NATIONAL_OPERATIONS


def needs_goods_full_data(operation_type):
    """Returns True if codTarifar, greutateNeta, valoareLeiFaraTva are required.
    Per Schematron BR-206/207/208 these are required for all operations
    except 60 and 70 (intra-community storage flows).
    """
    return operation_type not in NO_GOODS_DATA_OPERATIONS
