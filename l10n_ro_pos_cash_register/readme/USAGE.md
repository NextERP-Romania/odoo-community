# Daily use

## At the till

Tap **Cash Register** in the navigation bar. The sessions of that point of
sale are listed newest first, with the state of the ones still open, and
each line carries the register in figures:

| Column | What it is |
| --- | --- |
| Opening | the drawer counted when the session opened |
| Movements | everything written against it afterwards |
| Expected | the two added up — what the drawer should hold |
| Counted | what was actually counted at the close |
| Difference | counted less expected, in red when it is not zero |

**Cash Register** on a line hands over the document for that session.

The opening and the closing are not compared against the session's own
figures: `pos.session.opening_balance` and `closing_balance` are related
fields onto that very statement, so they could not disagree. The gap worth
looking at is the counted drawer against the movements, which is the
*Difference* column.

## In the back office

**Point of Sale → Orders → Sessions**, open a session, and the **Cash
Register** button is in the header. It prints the same document. The button
is not there for a session that kept no cash.
