# Key features

- **Full eTransport parity for batch transfers** — batch notifications go through the same ANAF Schematron v2.0.2 validation as individual transfer notifications.
- **Configurable price source per batch** — drive `valoareLeiFaraTva` from cost, purchase order, sale order, or list price.
- **Correct weights, UoM, and NC8 tariff codes** computed per move within the batch.
- **Street/number address split** on location addresses, satisfying ANAF schema requirements.
- **Multiple transport documents and previous notifications** on the batch form for operations 60/70.
- **Post-outage declaration flag** (OUG 41/2022 art. 8 par. 1³) directly on the batch.
- **Delete / Confirm / Modify Vehicle** ANAF actions available on the batch form via the shared action wizard.
- **Batch UIT reconciliation** included in the scheduled ANAF LIST sync cron job automatically.
