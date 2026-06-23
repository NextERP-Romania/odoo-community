# Romania - eTransport Extension

Fixes and extensions for the official Odoo `l10n_ro_edi_stock` module to align it with the ANAF eTransport v2 specification (XSD 2023-01-26, Schematron v2.0.2 from 2024-08-12).

The official module ships with several calculation bugs and missing features required by the current ANAF eTransport schema. This module corrects those issues and adds the full set of operations mandated by eTransport v2.0.2.

## Corrections to the official module

- **`valoareLeiFaraTva` (VAT-excluded value)** is computed correctly per operation direction:
  - *Incoming* (operations 10, 12, 14, 30-transfer, 40, 60): cost price from the stock move or, when a Purchase Order exists, `purchase.order.line.price_unit` converted to RON.
  - *Outgoing* (operations 20, 22, 24, 30-sale, 50, 70): sale price from `sale.order.line.price_unit` converted to RON, or `list_price` as fallback.
- **Quantity / UoM conversion** between `move.product_uom` and the declared `codUnitateMasura` is now consistent.
- **Gross weight** no longer doubles `shipping_weight` when a package has multiple `move_lines`; `greutateBruta >= greutateNeta` is always guaranteed.
- **`codTarifar`** (NC8/HS code) is required — the erroneous `00000000` fallback is removed.
- **`denumireStrada`** is correctly split from `numar / bloc / scara / etaj / apartament` per the `LocatieType` XSD definition.

## What this module provides

- **Flexible price source** (`l10n_ro_edi_stock_price_source` on `stock.picking`): *Automatic*, *Cost price*, *Purchase order price*, *Sale order price*, or *Product list price* — configurable per transfer or as a company-wide default.
- **Multiple transport documents per notification** (`l10n.ro.edi.stock.document.line`): `tipDocument` types 10 CMR / 20 Invoice / 30 Delivery note / 9999 Other, with free-text `remarks` for type 9999.
- **Previous notifications** (`l10n.ro.edi.stock.previous.notification`): `notificareAnterioara` entries required for operations 60/70 (DIN/DIE).
- **Post-outage declaration** (`l10n_ro_edi_stock_post_outage`): `declPostAvarie` flag per OUG 41/2022 art. 8 par. 1³.
- **Full UIT lifecycle wizard** (`l10n.ro.edi.stock.action.wizard`): Delete (DEL), Confirm (CON — confirmed / partially confirmed / refused), and Vehicle Modification (MVH) actions sent directly to ANAF.
- **LIST service sync** (`l10n.ro.edi.stock.list.wizard`): fetch and reconcile the ANAF notifications list for any date range (1–60 days); automatic reconciliation logs matched UITs in the transfer chatter. A scheduled cron job (`ir_cron_l10n_ro_edi_stock_list_sync`) runs every 6 hours.
- **Transporter Info service** (`l10n.ro.edi.stock.transporter.info.wizard`): query ANAF for all notifications in which the company acts as transport operator, with full vehicle and location details.
- **Extended document state tracking**: `l10n_ro_edi_stock_event_type` (NOT / COR / DEL / CON / MVH) and `l10n_ro_edi_stock_confirm_type` (10 / 20 / 30) stored on `l10n_ro_edi.document`.
