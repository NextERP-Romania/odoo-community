# Key features

- **Compliant with ANAF eTransport v2.0.2** — corrects value, weight, UoM, address and HS-code bugs in the official `l10n_ro_edi_stock` module.
- **Flexible VAT-excluded value calculation** — choose between Automatic, Cost, Purchase Order, Sale Order, or List price per transfer or as a company default.
- **Multiple transport documents per notification** — attach CMR, invoices, delivery notes or other documents to a single eTransport XML.
- **Full UIT lifecycle** — Delete, Confirm (confirmed / partially / refused), and Vehicle Modification actions sent directly to ANAF from the transfer.
- **Previous notification support** — `notificareAnterioara` entries for operations 60/70 (DIN/DIE).
- **Post-outage declaration flag** — `declPostAvarie` per OUG 41/2022 for submissions during ANAF system outages.
- **Automatic LIST sync cron** — reconciles ANAF notification list with local transfers every 6 hours; manual wizard also available.
- **Transporter Info service** — query ANAF for all notifications where the company acts as transport operator, with full vehicle and route details.
