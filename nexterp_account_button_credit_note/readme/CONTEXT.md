# Key features

- **Hides the Reverse button** on credit note forms (`out_refund` / `in_refund`) to prevent accidental double-reversal.
- **Hides the Create Invoice button** on credit note forms, keeping the UI clean and reducing operator errors.
- **Zero configuration** — rules are applied automatically through view inheritance on `account.move` after installation.
- **Standard invoice workflow unchanged** — buttons remain available on regular customer invoices and vendor bills.
- **Lightweight dependency** — extends only the core `account` module; no additional localization or third-party modules required.
