Keeps e-Factura invoices within the maximum text lengths ANAF accepts, so
an invoice is not refused because a name, an address or a note is too long.

- **Automatic shortening**: partner names and addresses, references,
  payment details, discount and charge reasons, VAT exemption reasons and
  product names and descriptions are cut to the lengths the Romanian
  e-invoicing rules allow.
- **Notes kept in full**: long invoice and line notes are not cut but split
  into several notes of the allowed size, so no text is lost.
- **Counted like ANAF counts**: lengths are measured in characters, the way
  the ANAF validator measures them, diacritics included.
- **Nothing to set up**: installed together with
  `l10n_ro_edi_extension`.
