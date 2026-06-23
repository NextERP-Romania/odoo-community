# Configuration

## 1. Company-wide default price source

1. Go to **Settings → Inventory** (or **Settings → Accounting**) and search for the **eTransport** section.
2. Set **Default eTransport Price Source** (`l10n_ro_edi_stock_default_price_source`) to the strategy that matches your typical operations:
   - *Automatic (by operation)* is recommended for mixed-use companies.
   - Override per transfer when needed using the field on `stock.picking`.

## 2. Automatic LIST sync (cron)

1. In the same settings page, tick **Automatic List Sync** (`l10n_ro_edi_stock_list_enabled`).
2. Set **List Sync Days** (`l10n_ro_edi_stock_list_days`, 1–60) — the number of days the cron looks back each run.
3. The scheduled action *eTransport: ANAF notifications list sync* (`ir_cron_l10n_ro_edi_stock_list_sync`) runs every 6 hours automatically once enabled. To adjust the interval, go to **Settings → Technical → Automation → Scheduled Actions** and edit the cron record.

## 3. Verify NC8/HS codes on products

Because `codTarifar` is now mandatory (the `00000000` fallback has been removed), ensure every product that appears on eTransport-eligible transfers has a valid 4-, 6-, or 8-digit HS/NC8 code set on the product form before sending notifications.

## 4. Verify address structure

The module splits Romanian street addresses into `denumireStrada` + number/building details automatically via `_l10n_ro_edi_stock_split_street`. Confirm that partner addresses follow the format *"Street name number"* (e.g. *"Calea Victoriei 12-14"*) to ensure correct splitting.
