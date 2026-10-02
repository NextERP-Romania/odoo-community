A shop keeping its takings in a drawer owes a *registru de casă* for every
day the drawer was open. A point of sale session is exactly that document in
another shape: it opens on a counted balance, every movement is written
against it, and it closes on another count.

This module hands that document over, from both ends:

- **at the till**, a *Cash Register* screen lists the sessions of the point
  of sale and prints the register of any of them, without anybody leaving
  the session or asking the back office;
- **in the back office**, the same button sits on the session form.

What is printed is not a second register form. A session with cash control
carries an `account.bank.statement` of its own -- core's `bank_statement_id`
-- and the Romanian register is already written for that model, in
`l10n_ro_account_bank_statement_report`. So the till and the bank print the
same paper, and there is no second implementation to drift away from the
first.

The list also carries the figures, so the question is answered without
opening the document: what was counted at the open, what moved, what the
drawer should hold, what was actually counted, and the gap between those
last two -- highlighted, because it is the only one that can surprise
anybody.
