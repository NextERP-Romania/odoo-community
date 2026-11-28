A point of sale normally runs one session at a time: open it, sell, close
it, open the next. A shop whose orders come in from an external back-end
does not always work that way: the day being synchronised is not always
the day that has just ended, and one register can have several days open
at once.

This module lets a register keep several sessions open and keeps the cash
right while it does.

- **Multiple Open Sessions**, switched on register by register; the other
  registers keep working as before.
- The register always works in the **oldest** open session, so a cashier
  reopening the till lands in the right day.
- A session opened from the list of sessions opens that session, not
  whichever was created last.
- When a session closes, the sessions still open after it get their
  opening balance rebuilt from its real closing balance, as long as their
  opening cash count has not been confirmed yet.
- Filling in the opening cash count keeps the opening time the session
  already has, so the open days stay in the order they happened.
