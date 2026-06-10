# Key features

- **Automatic inter-company flag** — `is_inter_company` stored computed field on `account.move` and related field on `account.move.line`, populated without manual intervention.
- **Search filters on Invoices & Bills** — quickly isolate customer invoices and vendor bills that are inter-company transactions.
- **Journal Entry filter** — filter all journal entries by inter-company status directly from the Journal Entries list view.
- **Journal Items filter** — drill down to individual debit/credit lines (`account.move.line`) belonging to inter-company moves.
- **Invoice Analysis integration** — segment the built-in Invoice Analysis report by inter-company vs. external transactions.
- **Built on `nexterp_inter_company`** — reuses the centralised partner/company grouping logic; no duplicate configuration required.
