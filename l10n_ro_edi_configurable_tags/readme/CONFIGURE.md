1. Grant *Manage e-Factura XML rules* to the people who maintain the mapping
   (Settings → Users → the user → *E-Factura XML*).
2. Create a profile under Accounting → Configuration → *e-Factura XML
   profiles* for each family of customers that asks for the same thing, and
   add its rules.
3. On the partner, open the *e-Factura XML* tab, pick the profile, and add
   there only the rules that are specific to that one partner.

A rule needs:

- **XML field** — the node, picked from the catalog. *Custom path* is reserved
  to the Settings group, for a node the catalog does not list yet.
- **Value from**:
  - *Field* — a dotted path read on the invoice, e.g. `partner_shipping_id.ref`,
    or on the invoice line for a line rule, e.g. `product_id.barcode`. A path
    crossing a one2many, such as `picking_ids.name`, joins the values with
    commas.
  - *Fixed text* — the same value for every invoice of this partner.
  - *Python expression* — reserved to the Settings group, for what a field path
    cannot express, e.g. `move.picking_ids[:1].name`.
  - *Remove the node* — drop what Odoo computed.
- **Applies to** — invoices, credit notes, or both. A node UBL only defines on
  one of the two is narrowed down automatically.
- **Overwrite** — on by default. Switch it off to fill the node only when Odoo
  left it empty.
- **Required** — block the export with an explicit error when the rule
  produces no value, instead of silently leaving the node out.
