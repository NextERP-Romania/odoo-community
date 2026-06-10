# Key features

- **Automatic accounting date alignment** — vendor bill accounting date is set to the invoice date whenever the fiscal period is open.
- **Tax lock date awareness** — if the invoice date falls inside a locked period, the accounting date is automatically shifted to `tax_lock_date + 1`, preventing illegal back-dating.
- **Zero configuration** — logic activates on install with no settings to adjust.
- **Transparent to users** — accountants work with invoice dates as usual; the module handles period compliance silently.
- **Lightweight `account` dependency** — no additional modules required beyond the standard Odoo Invoicing / Accounting app.
