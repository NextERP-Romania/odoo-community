# Configuration

The module exposes a single Boolean per journal. Setup is a one-time
review of every accounting journal that should — or should not — push
to SPV.

## 1. Install dependencies

The manifest depends on `l10n_ro_edi`. Make sure the Romanian EDI
module is installed and the company is fully set up for SPV
connectivity (certificate, ANAF credentials, EDI format selection)
before configuring journals.

## 2. Default behaviour after install

The flag `l10n_ro_edi_send_enabled` defaults to `False`. Right after
installing the module, **no journal is EDI-enabled** — including
journals that were sending EDI before. Plan the rollout so the
journals to keep on EDI are configured immediately.

## 3. Enable EDI per journal

Go to **Accounting → Configuration → Journals** and open each journal
you want to keep on EDI:

1. On the form, locate **Enable EDI Send** (right after **Currency**).
2. Tick the checkbox.
3. Save the journal.

Typical journals to enable:

- The default **Customer Invoices** journal of the Romanian company.
- Any additional sales journal that issues B2B invoices subject to
  SPV reporting.

Typical journals to leave disabled:

- Vendor bill journals (purchases are pulled by the ANAF API rather
  than pushed).
- Miscellaneous journals used for manual allocations.
- Intercompany / consolidation journals where invoices are mirrored
  from another database and have already been reported once.
- Test or training journals.

## 4. Verify in the move-send flow

1. Open **Accounting → Customers → Invoices** and create an invoice
   on a journal that has **Enable EDI Send** ticked.
2. Confirm and click **Send & Print**.
3. The EDI option appears in the wizard with the journal's setting.
4. Repeat on a journal where the flag is off — the EDI option is
   skipped because `_is_ro_edi_applicable` now returns `False`
   upstream.

## 5. User access

No new security groups are added. The journal field is editable by
users with the **Accounting: Adviser** group, like the rest of the
journal configuration.
