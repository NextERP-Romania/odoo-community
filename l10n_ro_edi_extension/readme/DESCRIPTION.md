Makes the daily e-Factura work with ANAF hands-off: customer invoices are
sent on their own after a waiting period you choose, their status is
fetched back regularly, and supplier invoices received in the SPV become
vendor bills.

- **Automatic sending**: posted invoices for Romanian customers are sent
  to ANAF once the waiting period has passed, so there is still time to
  correct them before they leave.
- **Status follow-up**: the answers from ANAF are fetched every hour for
  the invoices already sent.
- **Supplier invoices from the SPV**: bills received in the SPV are
  downloaded and created as vendor bills, without duplicates.
- **Send to ANAF from the list**: a **Send to ANAF** button on the customer
  invoice and credit note lists sends a selection in one go.
- **Error alerts**: the users you choose are notified whenever a sending
  fails.
- **Safe corrections**: an invoice sent to or validated in the SPV can no
  longer be reset to draft or cancelled; corrections go through a credit
  note. Refused invoices can still be reset and sent again.
- **Clean XML**: long names, descriptions and notes are adjusted so that
  ANAF does not refuse the invoice for oversized text.
