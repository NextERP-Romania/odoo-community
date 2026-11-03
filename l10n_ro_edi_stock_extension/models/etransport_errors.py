# Copyright 2026 NextERP Romania SRL
"""Read the schema (XSD) errors ANAF returns for a rejected eTransport file.

ANAF validates the upload with Xerces and answers with the raw parser text:

    Fisierul transmis nu este valid. org.xml.sax.SAXParseException;
    lineNumber: 25; columnNumber: 170; cvc-minLength-valid: Value '' with
    length = '0' is not facet-valid with respect to minLength '1' for type
    'Str200'.

The text names neither the element nor, often, the attribute. The position
does, though: it points into the very XML we sent, so the element can be found
there. The functions here only parse; turning the result into a message about
an Odoo record is done on stock.picking.
"""

import re

from lxml import etree

_SAX_ERROR = re.compile(
    r"lineNumber:\s*(?P<line>\d+);\s*columnNumber:\s*(?P<col>\d+);\s*"
    r"(?P<code>cvc-[\w.\-]+):\s*"
    r"(?P<text>[^\n]*?)(?=\s*(?:Fi[sș]ierul|org\.xml\.sax|lineNumber:)|\s*$)",
    re.M,
)
_VALUE = re.compile(r"Value '(?P<value>.*?)'")
_DATATYPE_VALUE = re.compile(r"^'(?P<value>.*?)' is not a valid value")
_ATTRIBUTE = re.compile(r"[Aa]ttribute '(?P<attribute>[\w:]+)'")
_ELEMENT = re.compile(r"element '(?P<element>[\w:]+)'")
_MAX_LENGTH = re.compile(r"maxLength '(?P<max>\d+)'")

# Error kinds the explanation understands
EMPTY = "empty"
MISSING = "missing"
TOO_LONG = "too_long"
INVALID = "invalid"


def _kind(code, value):
    if code == "cvc-complex-type.4":
        return MISSING
    if code == "cvc-minLength-valid" and value == "":
        return EMPTY
    if code == "cvc-maxLength-valid":
        return TOO_LONG
    if code in (
        "cvc-minLength-valid",
        "cvc-pattern-valid",
        "cvc-enumeration-valid",
        "cvc-attribute.3",
        "cvc-length-valid",
        "cvc-minInclusive-valid",
        "cvc-maxInclusive-valid",
        "cvc-minExclusive-valid",
        "cvc-maxExclusive-valid",
        "cvc-totalDigits-valid",
        "cvc-fractionDigits-valid",
    ) or code.startswith("cvc-datatype-valid"):
        return INVALID
    return None


def parse_xsd_errors(message):
    """Return one dict per Xerces error found in ``message``.

    Keys: line, col, code, kind (None when not understood), value, attribute,
    element, max_length, original. Missing information is None.
    """
    errors = []
    for match in _SAX_ERROR.finditer(message or ""):
        text = match["text"].strip()
        value = _VALUE.search(text) or _DATATYPE_VALUE.search(text)
        attribute = _ATTRIBUTE.search(text)
        element = _ELEMENT.search(text)
        max_length = _MAX_LENGTH.search(text)
        value = value["value"] if value else None
        errors.append(
            {
                "line": int(match["line"]),
                "col": int(match["col"]),
                "code": match["code"],
                "kind": _kind(match["code"], value),
                "value": value,
                "attribute": attribute["attribute"] if attribute else None,
                "element": element["element"] if element else None,
                "max_length": int(max_length["max"]) if max_length else None,
                "original": f"{match['code']}: {text}",
            }
        )
    return errors


def _local(tag):
    return etree.QName(tag).localname


def locate_element(raw_xml, line):
    """Find the element Xerces was on when it reported ``line``.

    Xerces reports the end of the start tag, so the element is the last one
    whose start tag begins on or before that line. Returns a dict with the
    element ``tag``, its ``attrs``, its ``parent`` tag and its ``index`` among
    the siblings of the same tag (0-based), or None if the XML can't be read.
    """
    if not raw_xml:
        return None
    if isinstance(raw_xml, str):
        raw_xml = raw_xml.encode()
    try:
        root = etree.fromstring(raw_xml)
    except etree.XMLSyntaxError:
        return None
    found = None
    for node in root.iter(etree.Element):
        if node.sourceline is not None and node.sourceline <= line:
            found = node
        elif node.sourceline is not None and node.sourceline > line:
            break
    if found is None:
        return None
    parent = found.getparent()
    siblings = (
        [n for n in parent if n.tag == found.tag] if parent is not None else [found]
    )
    return {
        "tag": _local(found.tag),
        "attrs": dict(found.attrib),
        "parent": _local(parent.tag) if parent is not None else None,
        "index": siblings.index(found),
    }


def guess_attribute(error, element):
    """The attribute an error is about: named by Xerces, or the one holding
    the rejected value. None when it can't be told."""
    if error["attribute"]:
        return error["attribute"]
    if element is None or error["value"] is None:
        return None
    candidates = [
        name for name, value in element["attrs"].items() if value == error["value"]
    ]
    return candidates[0] if len(candidates) == 1 else None
