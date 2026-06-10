Automate the attachment of bank statement lines to a parent bank
statement on Romanian companies. When a new line is created without a
`statement_id`, the module looks for an existing statement on the same
journal and date, creates one if it does not exist, and links the line
to it.

This avoids the manual step of opening or creating a daily statement
before importing bank transactions — useful for setups that ingest
statement lines through MT940 / CAMT.053 parsers, OCR uploads or
external feeds, where the source format only carries the line and not
its statement wrapper.

The behaviour is gated on the company's country code being `RO`, so
multi-company databases that mix Romanian and non-Romanian entities
keep the standard Odoo behaviour everywhere else.
