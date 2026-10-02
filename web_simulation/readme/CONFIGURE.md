Access is granted through the **Simulate Operations** group. Administrators
have it already.

Nothing else needs configuring. A simulation happens inside one request on one
cursor, so any server works, with any number of workers.

Two things are worth knowing:

- **module installs and upgrades are refused** during a simulation, because a
  schema change cannot be rolled back with the rest;
- **no mail is sent and no external service is called**: the after-commit
  hooks queued by the run are dropped, since those are exactly the ones that
  cannot be undone.

Document numbering is not affected. A simulation does not draw from the real
sequence; it reads what the next number would be and counts on its own, so
documents carry the numbers they would have got and the sequence is left where
it was. Invoices never used `ir.sequence` anyway: their number comes from a
query over the existing invoices, and it is rolled back with everything else.
