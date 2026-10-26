Takes in from the SPV the self-invoices (*autofacturi*) your customers issue in your name.

Such an invoice is uploaded by the customer, but it carries your company as supplier and the customer as buyer: it is a sale of yours, not a vendor bill. Without this module, the SPV synchronization would import it as a bill.

- It is recognised from the XML: the supplier is your company and the buyer is somebody else. A document listed as sent counts only when it carries the self-billing type code 389, so your own invoices are never mistaken for one.
- It becomes a customer invoice. In the customer's self-invoicing journal it keeps the number the customer gave it and is posted; without such a journal it is a draft in the first sale journal.
- It is marked as validated in the SPV, so it is never sent to ANAF again, and a later synchronization does not duplicate it.
- Both synchronizations take it in: the `l10n_ro_edi` one and the SPV messages of `l10n_ro_message_spv`.

It also covers the other direction, the self-invoices you issue in your suppliers' name: their credit notes go to the SPV with `CreditNoteTypeCode` 381, the only one CIUS-RO accepts, instead of the 261 Odoo sets on self-billing credit notes.
