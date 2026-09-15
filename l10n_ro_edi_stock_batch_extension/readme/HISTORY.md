# Changelog

## 19.0.1.2.0 (2026-09-15)

- Keep a picking sendable to eTransport while its batch is still in progress
  and has not been notified itself. `l10n_ro_edi_stock_batch` disables
  eTransport on every picking belonging to a batch, which defeated sending the
  notification before the goods move.

## 19.0.1.0.0 (2026-06-23)

- _Changelog tracking starts at this release._
