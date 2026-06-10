# Daily use

Once the journals are configured, users do not interact with this
module directly. The behaviour shows up implicitly in the
**Send & Print** flow and in the EDI reporting screens.

## Posting an EDI-eligible invoice

1. Go to **Accounting → Customers → Invoices** and create or open an
   invoice on a journal where **Enable EDI Send** is ticked.
2. Confirm the invoice.
3. Click **Send & Print**.
4. The EDI option is offered by `l10n_ro_edi` like in the standard
   flow; sending the invoice produces an `account.edi.document` and
   uploads it to ANAF / SPV.

## Posting on a non-EDI journal

1. Open or create an invoice on a journal where **Enable EDI Send** is
   unticked.
2. Confirm and click **Send & Print**.
3. The EDI checkbox does not appear (or is hidden as not applicable),
   because `account.move.send._is_ro_edi_applicable` returns `False`
   for that journal.
4. The invoice is sent by email / printed as a normal PDF without any
   ANAF upload.

## Changing the setting

The flag can be toggled at any time on **Accounting → Configuration →
Journals**:

- Turning it **on** makes new postings on that journal EDI-eligible,
  starting from the next save.
- Turning it **off** stops new postings from being submitted; EDI
  documents already generated for past moves remain attached to those
  moves and are not deleted.

## Multi-company

The override looks at the journal of the move, not the company
directly. In a multi-company database each company's journals must be
configured separately; switching companies in the top bar then opening
**Accounting → Configuration → Journals** shows the journals of the
active company.

## What the user does not see

- The override is silent — there is no warning popup when an invoice
  is posted on a non-EDI journal.
- The journal flag is not visible from the invoice itself; users
  needing to check it must open the journal record.
