=================================
Romania - eTransport Batch Extension
=================================

This module brings the facilities of ``l10n_ro_edi_stock_extension`` to
**batch transfers** (``stock.picking.batch``), so that an eTransport
notification sent from a batch behaves exactly like one sent from a single
transfer.

On top of the base ``l10n_ro_edi_stock_batch`` it adds, for batches:

* Stricter validation per ANAF Schematron v2.0.2 (operation scope vs operation
  type, partner country code, mandatory tariff code / weights / value, previous
  notifications for operations 60/70).
* Correct ``valoareLeiFaraTva`` through a configurable **price source**
  (automatic / cost / purchase / sale / list).
* Correct net and gross weights, quantity and unit of measure, and ``codTarifar``
  (NC8) per move.
* Street / number split on the location addresses.
* Multiple ``documenteTransport`` entries and ``notificareAnterioara`` entries.
* Post-outage declaration flag (``declPostAvarie``).
* The **Delete / Confirm / Modify vehicle** ANAF actions on the batch form.
* Reconciliation of batch UITs in the ANAF LIST cron job.

Technically the batch reuses the picking-level logic of
``l10n_ro_edi_stock_extension``: the batch is injected as the
``_picking_record`` used by the extension's validation and template
enrichment, and implements the same helper interface.
