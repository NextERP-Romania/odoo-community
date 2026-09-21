# Usage

## Opening and working through multiple sessions on one register

This workflow applies to registers where **Multiple Open Sessions** (`pos_multi_session`) is enabled.

1. Go to **Point of Sale → Configuration → Settings**, select the register, and confirm that **Multiple Open Sessions** is turned on (see CONFIGURE for details).
2. Open a session as normal. Odoo creates Session A (e.g. for Monday).
3. When the back-end pushes orders for a new day before Monday is closed, open a second session. Session B (Tuesday) is created alongside Session A — no conflict.
4. The register always lands the cashier in the **oldest open session** (Session A). The till works through days in the order they started, not the order they were last touched.
5. To close, the cashier closes Session A first. Odoo rebuilds Session B's opening balance from Session A's real closing balance automatically.
6. Close Session B next. If a Session C exists, its opening balance is updated in the same way.

> **Rule:** sessions must be closed oldest-first. Attempting to open a new session while an older one is still open is blocked — the new session's opening balance would have nothing real to start from.

## Reopening a register mid-chain

If a cashier closes the browser and comes back:

1. Navigate to **Point of Sale → Dashboard** and click **Open** on the register.
2. Odoo routes the cashier into the oldest open session automatically — no manual selection needed.

## Reviewing session statistics

Statistics reported via `get_statistics_for_session` always reflect the **oldest open session**, keeping the cash summary aligned with the day the till is actively working through.
