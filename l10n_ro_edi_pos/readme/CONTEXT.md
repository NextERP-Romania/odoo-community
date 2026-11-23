# Key features

- **Automatic type-code 751** — invoices that carry a `l10n_ro_fiscal_receipt_number` are exported to RO e-Factura as *Factură — informații în scopuri contabile*, as required by ANAF.
- **Fiscal Receipt Number on POS orders** — the register's driver fills `l10n_ro_fiscal_receipt_number` on `pos.order`; the value propagates automatically to the customer invoice.
- **Manual override for back-office invoices** — accountants can type the receipt number directly in the invoice's *Other Info* tab before sending to the SPV.
- **Field locked after SPV submission** — the receipt number (and therefore the e-Factura type code) cannot be changed once the invoice has been sent to ANAF, preventing inconsistencies.
- **Non-intrusive** — invoices without a receipt number and all credit notes keep their standard type codes; no configuration is required after installation.
