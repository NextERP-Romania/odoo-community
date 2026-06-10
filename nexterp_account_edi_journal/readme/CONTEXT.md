# Key features

- **Per-journal EDI switch** — adds the Boolean field
  `l10n_ro_edi_send_enabled` on `account.journal`, defaulting to
  `False`, so existing journals do not start sending EDI documents
  silently after the module is installed.
- **Form integration** — the field is injected into the standard
  journal form view right after `currency_id`, keeping it visible in
  the same area as the other journal configuration toggles.
- **Send-flow guard** — overrides `account.move.send._is_ro_edi_applicable`
  so the move is considered non-applicable as soon as
  `move.journal_id.l10n_ro_edi_send_enabled` is `False`; the rest of
  the upstream conditions still apply when the flag is on.
- **No new menus or wizards** — the feature is purely configuration on
  existing screens; there is nothing to open or trigger separately.
- **Romanian-EDI dependency** — depends on `l10n_ro_edi`, which
  carries the SPV / e-Factura connectivity, EDI document model and
  default applicability logic.
- **Safe default** — because the new flag defaults to `False`, every
  journal must be explicitly opted in. Existing setups stop sending
  EDI until journals are configured.
- **Backwards-compatible with EDI logs** — the override only blocks
  applicability; it does not delete or alter EDI documents already
  attached to past moves.
