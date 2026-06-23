# Romania - eTransport Batch Extension

Extends eTransport (e-Transport) EDI notifications to **batch transfers** (`stock.picking.batch`), bringing the full feature set of `l10n_ro_edi_stock_extension` to multi-picking shipments declared together to ANAF.

By default, the base `l10n_ro_edi_stock_batch` module can send a single UIT notification for a batch, but it lacks the stricter validation and enrichment that `l10n_ro_edi_stock_extension` provides for individual transfers. This module bridges that gap: a batch notification sent through this module is treated identically to a single-transfer notification, satisfying ANAF Schematron v2.0.2 requirements.

## What this module provides

- **Schematron v2.0.2 validation for batches** — operation scope vs operation type, partner country code, mandatory tariff code (`codTarifar` / NC8), weights, values, and previous notification references for operations 60/70.
- **Configurable price source** (`l10n_ro_edi_stock_price_source`) on the batch — choose between *Automatic (by operation)*, *Cost price*, *Purchase order price*, *Sale order price*, or *Product list price* to drive the `valoareLeiFaraTva` field sent to ANAF.
- **Correct per-move data**: net and gross weight computation, quantity and unit of measure (`_l10n_ro_edi_stock_get_qty_and_uom`), and NC8 tariff code (`_l10n_ro_edi_stock_get_codtarifar`).
- **Street / number split** on location addresses (`_l10n_ro_edi_stock_split_street`) per ANAF schema.
- **Multiple transport document entries** (`l10n_ro_edi_stock_document_line_ids`) and **previous notification entries** (`l10n_ro_edi_stock_previous_ids`) directly on the batch form.
- **Post-outage declaration flag** (`l10n_ro_edi_stock_post_outage`) — OUG 41/2022 art. 8 par. 1³, allowing late declaration until end of the next working day after ANAF system recovery.
- **Full ANAF action wizard** on the batch form — *Send*, *Delete*, *Confirm*, and *Modify Vehicle* actions (`l10n.ro.edi.stock.action.wizard`) extended to work against a `stock.picking.batch` instead of a single picking.
- **Batch UIT reconciliation** in the ANAF LIST cron job — batch UITs are picked up alongside individual transfer UITs during the scheduled sync (`_l10n_ro_edi_stock_list_sync_one`).

Technically, the batch record is injected as the `_picking_record` consumed by `l10n_ro_edi_stock_extension`'s validation and XML template pipeline, implementing the same helper interface so no duplicate logic is needed.
