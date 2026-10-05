# Romania - E-invoicing Configurable Tags

Fills CIUS-RO (e-Factura) XML nodes differently for each partner, from the
interface, without a new module per customer.

Odoo always builds the same XML for everyone, while buyers do not ask for the
same thing: a retailer reconciles on its own purchase order number and its own
article codes, a public institution wants the tender reference, another one
wants its cost centre in the buyer accounting reference. Until now each of
these meant either a Studio field wired to a single node, or a dedicated
Python flavour of the UBL builder.

## What this module provides

- **A catalog of CIUS-RO nodes** (`tools/ciusro_fields.py`) — the ~30 business
  terms a partner commonly asks for, each with its UBL path, its schematron
  length limit and a short explanation. It plays the role Odoo's
  `PEPPOL_COMMON_OPTIONAL_FIELDS` plays for Peppol, except the value is not
  bound to a fixed Studio field.
- **Rules** (`l10n_ro.edi.xml.rule`) — one line per node to fill: which node,
  where its value comes from (a field of the invoice or the invoice line, a
  fixed text, or a Python expression), on which document types, and whether it
  replaces or only completes what Odoo computed. A rule can also remove a node
  the partner refuses.
- **Profiles** (`l10n_ro.edi.xml.profile`) — a reusable set of rules attached
  to the partners that share the same requirements, exportable as JSON so the
  same setup can be replayed on another database.
- **A dedicated group** — *Manage e-Factura XML rules*. It is granted to
  nobody by default: the rules decide what is filed with ANAF, so editing them
  is a deliberate permission, not a side effect of being allowed to edit a
  partner. The *e-Factura XML* tab on the partner and the profiles menu are
  only visible to that group.
- **Export-time validation** — a path that does not exist in the UBL template
  is refused when the rule is saved, instead of breaking the XML rendering at
  send time, and a rule marked as required blocks the export with an explicit
  message when it produces no value.
