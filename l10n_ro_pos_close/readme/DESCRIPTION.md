A session of a point of sale is closed by counting: the cashier declares,
for each payment method, the amount actually in hand. Odoo compares that with
what the register recorded, posts the gap to the profit or loss account of the
journal, and keeps neither number. What is left in the database is a
correction entry nobody can read back.

A shop has to be able to say *why*. The common case is not a missing leu but a
misplaced one: an order cashed in on the card method while the customer paid
in cash, which leaves the card short by exactly what the drawer holds too
much. The takings are complete, their split between the payment methods is
not, and somebody has to state that in writing.

This module keeps the closing control and turns it into that statement:

- when a session is closed, one line per payment method records what the
  register expected, what the cashier counted and the difference between
  them. Methods the register did not count are left out, as core leaves them
  out of the reconciliation;
- the closing popup of the register asks the cashier, for every method that
  did not match, what happened: a cause and a sentence of explanation. That
  is the moment somebody still knows, and the closing note typed in the same
  popup -- which Odoo collects and then drops on the way to the server -- is
  kept with it;
- a session that did not match is flagged in the chatter, method by method,
  as soon as it closes, and what was not explained at the register can be
  completed afterwards from the session;
- **Report of Differences** prints the lot as the record a Romanian shop
  files for it (*proces verbal de constatare a diferențelor la închiderea
  sesiunii de casă*): the methods, the amounts, the causes, the note and the
  signatures. When the surpluses cover the shortages in full, the report says
  so in as many words: the takings are whole, only recorded on the wrong
  method.

The accounting itself is untouched. Core posts the differences as it always
did; this module only explains them.
