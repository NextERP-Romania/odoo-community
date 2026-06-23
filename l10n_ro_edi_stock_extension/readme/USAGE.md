# Usage

## Configuring the price source for a transfer

1. Open a validated or in-progress transfer in **Inventory → Transfers**.
2. In the **eTransport** tab, locate the **eTransport Price Source** field (`l10n_ro_edi_stock_price_source`).
3. Choose one of:
   - *Automatic (by operation)* — cost on incoming/internal, sale price on outgoing.
   - *Cost price* — always uses `standard_price`.
   - *Purchase order price* — pulls from the linked PO line in RON.
   - *Sale order price* — pulls from the linked SO line in RON.
   - *Product list price* — uses `list_price`.
4. Continue with the normal eTransport notification flow.

## Adding transport documents (CMR, Invoice, etc.)

1. Open the transfer and go to the **eTransport** tab.
2. Under **Transport Documents**, click **Add a line**.
3. Set **Document Type** (10 CMR / 20 Invoice / 30 Delivery Note / 9999 Other), **Document Number**, and **Document Date**.
4. If type is *Other (9999)*, fill in the **Remarks** field (required by ANAF).
5. Add as many documents as needed; all will be included in the XML notification.

## Declaring previous notifications (operations 60/70)

1. On the transfer, go to the **eTransport** tab → **Previous Notifications** section.
2. Click **Add a line** and enter the **Previous UIT**, optional **Remarks**, and **Declarant Reference**.
3. These entries are serialised as `notificareAnterioara` elements in the XML sent to ANAF.

## Marking a post-outage declaration

1. On the transfer **eTransport** tab, tick **Post-Outage Declaration** (`l10n_ro_edi_stock_post_outage`).
2. This sets `declPostAvarie=1` in the submitted XML, allowed until the end of the next working day after an ANAF system outage (OUG 41/2022 art. 8 par. 1³).

## Performing UIT lifecycle actions (Delete / Confirm / Modify vehicle)

After a notification UIT has been obtained:

1. Open the transfer and use the action buttons in the **eTransport** tab (or the action menu).
2. **Delete notification** — opens `l10n.ro.edi.stock.action.wizard` pre-set to *DEL*; confirm to send the deletion to ANAF.
3. **Confirm transport** — opens the wizard pre-set to *CON*; choose confirmation type (10 Confirmed / 20 Partially confirmed / 30 Refused) and submit.
4. **Modify vehicle** — opens the wizard pre-set to *MVH*; enter the new vehicle number, optional trailer numbers, and modification date/time.
5. The wizard calls `_upload_and_log`, posts the ANAF response in the chatter, and updates `l10n_ro_edi_stock_event_type` on the related `l10n_ro_edi.document` record.

## Syncing the ANAF notifications list manually

1. Go to **Inventory → Operations → eTransport notifications list** (`menu_l10n_ro_edi_stock_list_wizard`).
2. Enter the **Number of days** (1–60) to look back.
3. Click **Fetch** (`action_fetch`). The wizard retrieves the ANAF LIST and displays all returned notifications as `l10n.ro.edi.stock.list.line` records.
4. Click **Reconcile** to automatically match UITs to local transfers and log the result in each transfer's chatter.

## Querying transporter info (as transport operator)

1. Go to **Inventory → Operations → Notifications as transport operator** (`menu_l10n_ro_edi_stock_transporter_info_wizard`).
2. Fill in **Transport operator VAT**, and optionally **Initial declarant VAT**, **Specific UIT**, or **Declarant reference**.
3. Click **Fetch** (`action_fetch`). Each matching ANAF notification appears as an `l10n.ro.edi.stock.transporter.info.line` row with UIT, vehicle numbers, start/end locations, and expiry date.
