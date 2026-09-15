Odoo runs one session at a time on a Point of Sale: open it, sell, close it,
open the next. A shop whose orders arrive from an external back-end does not
work that way -- the day it is syncing is not always the day that has just
ended, and a register can have several days open at once.

This module lets that happen, and keeps the cash honest while it does:

- the register's *current* session is the **oldest** one still open, not the
  newest. That is the day the till is working through, and the one a cashier
  reopening it lands in;
- a new session cannot be opened while an older one is still open, because
  its opening balance would have nothing real to start from;
- when a session closes, every session still open behind it has its opening
  balance rebuilt from the real end balance of the session before it. While
  an earlier one is still open that balance is zero, and it becomes real as
  the chain closes down, oldest first;
- the opening time a session already carries is kept when the cash control is
  filled in, so filling it does not reorder the register's open days.
