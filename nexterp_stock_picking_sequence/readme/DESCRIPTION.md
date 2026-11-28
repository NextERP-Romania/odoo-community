A transfer takes the next number of its operation type as soon as it is
created. Transfers prepared and then cancelled or deleted leave holes in
the numbering of receipts and delivery notes.

With this module a transfer gets a draft name when it is created and its
real number only when it is validated, in the order the transfers are
done.

- Draft name on creation, taken from a separate draft sequence.
- Final number from the operation type's own sequence, given on
  validation.
- No gaps left by cancelled or deleted transfers.
- Switched on per company; companies that leave it off keep numbering on
  creation.
