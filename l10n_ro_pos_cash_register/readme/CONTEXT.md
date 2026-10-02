# Key features

- **A screen of its own** — *Cash Register* in the point of sale navigation,
  listing the sessions of that till newest first, searchable by session or
  cashier.
- **The register of a session, printed from the till** — one button per
  line, handing over the Romanian register form through the point of sale's
  own report service.
- **The same button in the back office** — on the session form, hidden where
  the session kept no cash.
- **One register form, not two** — the report printed is
  `l10n_ro_account_bank_statement_report.action_report_l10n_ro_account_statement`,
  run on `pos.session.bank_statement_id`. Nothing about the layout is
  reimplemented here.
- **The figures next to each session** — opening, movements, expected,
  counted, and the difference between the last two, shown in red when it is
  not zero.
- **Sessions without cash are said to be so** — a point of sale without cash
  control has no statement and no register; the row says it and the button
  is disabled instead of printing an empty form.
