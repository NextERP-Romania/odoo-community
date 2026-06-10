`nexterp_delivery_slip_report` customises the standard Odoo delivery
slip PDF (`stock.report_delivery_document`) and its variants for serial
numbers and aggregated lines. It does not introduce a new report
action — instead, it inherits the existing templates at priority 100
and changes their rendering based on three company-level switches.

The module addresses two recurring requests on warehouse paperwork:
the product column should print only the product name (without the
`[CODE] Name` display name and without the picking description), and
the quantity column should honour the per-UoM decimal precision
already exposed by `nexterp_account_invoice_report` (a dependency).

A third option drives the language of incoming / internal transfers:
when enabled, the printed slip uses the company partner's language for
non-outgoing pickings, while customer deliveries (`outgoing`) keep the
standard behaviour of using the customer language. All three options
are stored on `res.company` and are configurable under the Inventory
settings.
