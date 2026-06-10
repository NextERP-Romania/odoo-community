# Key features

- **Country-scoped automation** — the create override on
  `account.bank.statement.line` runs only when the company's country
  code is `RO`, leaving other localisations untouched.
- **Date + journal grouping** — a new line without `statement_id` is
  attached to the existing `account.bank.statement` that matches its
  `journal_id` and `date`; one statement per journal per day.
- **On-demand statement creation** — if no matching statement exists,
  one is created with the line's date used as both `date` and `name`,
  then linked to the line.
- **Balance recomputation** — after the link is set, the module
  triggers `_compute_balance_end` and `_compute_balance_end_real` on
  the statement so the running balance stays consistent with the new
  line.
- **Batch-friendly** — implemented through `@api.model_create_multi`,
  the override processes each record of a multi-create call
  individually, which keeps it compatible with bulk imports from
  parsers and connectors.
- **No new UI** — the module adds no fields, views, menus or
  configuration; behaviour is automatic on record creation.
- **No data files** — installation simply loads the model override;
  there is nothing to seed or migrate.
