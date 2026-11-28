## 19.0.1.3.2

- Apps listing: English description, configuration and usage, new icon and cover.

## 19.0.1.2.0

- The module no longer depends on `l10n_ro_message_spv`, so its license
  matches its dependencies. The company setting "Maximum number of days to
  download e-invoices" is now defined here as well.

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

- The type code of self-billing credit notes moved to `l10n_ro_edi_autoinvoice`, with the rest of the self-invoicing.

## 19.0.1.0.1 (2026-05-28)

- _Changelog tracking starts at this release._
