# Usage

## Sending an outgoing invoice to ANAF

### Automatic (cron)

Once the module is installed and configured, the cron job **Romania - Send Invoices to ANAF** runs on a schedule and submits all confirmed, unsent invoices automatically. No manual action is required for routine operation.

### Manual send from the invoice

1. Open the invoice: **Accounting → Customers → Invoices**.
2. Confirm the invoice (status **Posted**).
3. Click **Send & Print** → the Romanian EDI channel is pre-selected by default.
4. Alternatively, use the dedicated **Send to ANAF** button (`action_send_and_print_anaf`) on the invoice form to submit immediately and generate the PDF in one step.
5. The invoice status bar and the chatter show the ANAF submission result. If an error occurs, the users configured in **EDI Error Notify Users** receive an internal notification.

## Receiving supplier bills from SPV

1. The cron `_l10n_ro_edi_fetch_invoices` runs periodically and queries the SPV for new inbound messages.
2. For each new message, `_l10n_ro_edi_process_bill_messages` creates a draft `account.move` (vendor bill) in **Accounting → Vendors → Bills** if the bill does not already exist.
3. Open the generated draft bill, verify the lines, and confirm as usual.

## Receiving self-invoices issued by customers in your name

Some customers issue the invoice themselves, in your name, and upload it to the SPV (*autofactura*). In the SPV it carries your company as supplier and the customer as buyer, so it is a sale, not a bill.

1. Both SPV synchronizations recognise it from the XML: the supplier is your company and the buyer is somebody else. A document listed as sent counts only when it also carries the self-billing type code 389.
2. It becomes a customer invoice, never a vendor bill:
   - in the sale journal of type **Customer Auto Invoicing** set up for that customer, it keeps the number the customer gave it and is posted;
   - without such a journal, it is created as a draft in the first sale journal.
3. The invoice is marked as validated in the SPV, so it is never sent to ANAF again.
4. In **SPV Messages** these messages are ticked **Self-Invoice**; **Create Invoice** creates them the same way.

## Monitoring EDI errors

- Users listed in **EDI Error Notify Users** (see CONFIGURE) automatically receive Odoo internal messages when a submission to ANAF fails.
- Check the invoice chatter for the full error response returned by ANAF.
