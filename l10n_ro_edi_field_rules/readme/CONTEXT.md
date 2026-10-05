CIUS-RO still builds its XML through the `ubl_20` skeleton
(`_get_invoice_node`), even though each of its sections is now delegated to the
newer `_ubl_add_*` methods. That skeleton ends the document and every line with
the extension points Odoo uses for its own Peppol optional fields
(`_add_invoice_optional_nodes`, `_add_invoice_line_optional_nodes`); this module
hooks there, so the rules see a finished node tree and can complete or correct
it.

Order is not a concern: `dict_to_xml` takes the tag order from the UBL
template, not from the order in which keys were inserted. The same helper
raises a `ValueError` on a tag missing from the template, which is why a rule
validates its path against `ubl_21_invoice.py` / `ubl_21_credit_note.py` when
it is saved.
