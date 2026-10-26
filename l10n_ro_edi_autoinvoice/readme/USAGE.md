Nothing to do by hand: the SPV synchronizations take the self-invoices in as they arrive.

1. The scheduled synchronization of `l10n_ro_edi` creates them directly as customer invoices.
2. In **SPV Messages** they are ticked **Self-Invoice**; **Create Invoice** creates them the same way.
3. A self-invoice posted in the customer's journal carries the customer's number. One left in draft says why in its chatter: no journal for the customer, or the error that stopped the posting.
