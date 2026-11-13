# Changelog

## 19.0.1.2.0

- The module no longer depends on `l10n_ro_message_spv` (AGPL-3), so its
  LGPL-3 license is consistent with its dependencies. The company setting
  "Maximum number of days to download e-invoices" is defined here as well,
  with the same definition, and the override that routed the SPV message
  download of `l10n_ro_message_spv` through this module's paginated fetch was
  dropped — `l10n_ro_message_spv` uses its own paginated implementation.

## 19.0.1.1.1

- The XML that comes back from the SPV is parsed with entity resolution, DTD
  loading and network access switched off, and an archive member that
  unpacks to more than 64 MB is refused instead of being read into memory.

## 19.0.1.1.0 (2026-11-05)

- A customer invoice or credit note sent to the SPV or validated there can no
  longer be reset to draft or cancelled, not even through the server action
  (Odoo only hid the button). Refused or not indexed invoices can still be
  reset and sent again; corrections go through a credit note.

## 19.0.1.0.4 (2026-10-26)

- The `CreditNoteTypeCode` 381 on self-billing credit notes moved to `l10n_ro_edi_autoinvoice`, with the rest of the self-invoicing.

## 19.0.1.0.1 (2026-05-28)

- _Changelog tracking starts at this release._
