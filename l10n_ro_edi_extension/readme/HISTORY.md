# Changelog

## 20.0.1.2.0

- The module no longer depends on `l10n_ro_message_spv` (AGPL-3), so its
  LGPL-3 license is consistent with its dependencies, and it is installable
  again on 20.0 (it was disabled only because `l10n_ro_message_spv` has not
  been migrated to this series yet). The company setting "Maximum number of
  days to download e-invoices" is defined here as well, with the same
  definition, and the override that routed the SPV message download of
  `l10n_ro_message_spv` through this module's paginated fetch was dropped.

## 20.0.1.1.0 (2026-11-06)

- A customer invoice or credit note sent to the SPV or validated there can no
  longer be reset to draft or cancelled, not even through the server action
  (Odoo only hid the button). Refused or not indexed invoices can still be
  reset and sent again; corrections go through a credit note.

## 19.0.1.0.1 (2026-05-28)

- _Changelog tracking starts at this release._
