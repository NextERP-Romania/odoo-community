# Configuration

This module relies on `nexterp_inter_company` to determine which partners or companies are considered part of the same group. Before using the accounting filters, complete the inter-company partner setup in that base module.

1. Install `nexterp_inter_company` and configure your group companies/partners as inter-company entities according to its instructions.
2. Install `nexterp_inter_company_account`. The `is_inter_company` stored computed field is created automatically on both `account.move` and `account.move.line` via `_auto_init` — no manual field configuration is required.
3. No additional accounting settings are needed. The search filters become available immediately on Invoices, Journal Entries, Journal Items, and Invoice Analysis.
