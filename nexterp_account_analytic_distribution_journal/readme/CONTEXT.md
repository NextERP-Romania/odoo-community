# Key features

- **Journal-scoped analytic distribution** — pin any analytic distribution model to a specific journal so it fires only for lines posted in that journal.
- **Fully backward-compatible** — models with no journal set continue to apply to all journals, preserving existing behaviour.
- **No extra configuration** — the `journal_id` field is added directly to the existing `account.analytic.distribution.model` form and list views.
- **Granular cost allocation** — separate analytic plans per journal type (e.g. sales vs. purchases vs. bank) without writing custom code.
- **Lightweight extension** — depends only on the standard `account` module; no additional apps required.
