# Key features

- **Multiple open sessions per register** — let a POS register hold several days open simultaneously, suited for shops driven by an external order back-end.
- **Oldest-first discipline** — the register's *current* session is always the oldest one still open; cashiers land in the right day automatically.
- **Blocked out-of-order opens** — a new session cannot start while an older one is still open, preventing cash-carry miscounts.
- **Automatic opening-balance cascade** — closing the oldest session immediately rebuilds the opening balance of every session still open behind it.
- **Preserved opening timestamps** — filling in the cash control drawer does not alter the time the session already recorded, keeping day order intact.
- **Per-register opt-in** — `pos_multi_session` is toggled individually per register; unaffected registers keep standard Odoo behaviour.
