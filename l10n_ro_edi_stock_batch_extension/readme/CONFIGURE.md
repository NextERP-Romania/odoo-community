# Configuration

This module requires no dedicated configuration steps beyond installing its two dependencies (`l10n_ro_edi_stock_batch` and `l10n_ro_edi_stock_extension`). All configuration required for those modules (ANAF credentials, eTransport product settings, warehouse addresses) applies equally to batch transfers.

The only batch-specific setting is the **eTransport Price Source** field on each batch transfer form, which defaults to *Automatic (by operation)* via `_l10n_ro_edi_stock_default_price_source`. Change it per batch as needed before sending the notification.
