When a point of sale session is closed, the cashier counts what is in hand
for each payment method and Odoo posts the difference. The module keeps
that count and explains it: what was expected, what was counted, why they
differ, in a report the shop can sign and file.

The most common case is not missing money but money recorded on the wrong
method, such as a cash payment entered as card. The takings are complete,
only their split is wrong, and the report says so in writing.

- **Closing control per payment method**: expected amount, counted amount
  and difference, kept on the session.
- **Asked at the register**: for each method that does not match, the
  closing popup asks for a cause and an explanation, while somebody still
  remembers.
- **Closing note kept**: the note typed in the closing popup is saved.
- **Flagged in the chatter**: a session closed out of balance lists the
  methods that did not match.
- **Completed later**: what was not explained at the register can be added
  from the session.
- **Report of Differences**: methods, amounts, causes, note and
  signatures, stating clearly when surpluses cover shortages.
- **Accounting unchanged**: differences are posted as before; the module
  only explains them.
