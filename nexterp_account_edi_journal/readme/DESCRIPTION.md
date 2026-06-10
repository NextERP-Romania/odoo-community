Add a per-journal switch that controls whether moves posted in that
journal are eligible for Romanian e-invoicing (e-Factura / SPV). The
standard `l10n_ro_edi` flow applies the EDI check to every customer
invoice on a Romanian company; this module makes the decision explicit
at the journal level so internal, manual or out-of-scope journals can
opt out without disabling the whole feature.

The change is minimal: one Boolean field `l10n_ro_edi_send_enabled` on
`account.journal`, a small form override to surface it next to the
journal currency, and a guard in `account.move.send._is_ro_edi_applicable`
that returns `False` when the move's journal has the flag unchecked.
All other Odoo behaviour around EDI sending is unchanged.

Use this module when the database has several sales / miscellaneous
journals and only some of them are subject to SPV reporting — for
example, intercompany sales, internal allocations or test journals
that should never be uploaded to ANAF.
