# Key features

- **Closing control model** — `l10n.ro.pos.closing.line` holds, per session
  and payment method, `expected_amount`, `counted_amount`, the computed
  `difference` (counted less expected, so a positive amount is a surplus),
  the `reason` and a free `note`.
- **Capture on the way through** — `close_session_from_ui` flags the call and
  `_handle_cash_statement_entries` writes the lines just before core posts
  the cash correction, which is the last moment the drawer is still the one
  the cashier counted and the sales have already reached the statement.
- **Expected amount** — the payments of the session for a bank method, the
  end balance of the cash statement for the cash method: the same figures
  core compares the count against.
- **Methods left out** — a bank method the register did not send is skipped,
  as core skips its reconciliation; the cash method is always controlled,
  an uncounted drawer counting as empty. Methods that are neither cash nor
  bank (pay later) are not controlled at all.
- **Session totals** — `l10n_ro_closing_surplus`, `l10n_ro_closing_shortage`,
  `l10n_ro_closing_difference` and `l10n_ro_has_closing_difference` are
  stored on `pos.session`, so differences can be searched and grouped.
- **Asked at the register** — the closing popup gains, for each payment
  method whose count does not match, a cause and an explanation. They are
  sent by `l10n_ro_set_closing_explanations` just before core closes the
  session, parked on `l10n_ro_closing_explanations` and written on the
  control lines as they are created. The cause is checked against the
  selection, since it comes from a browser.
- **The closing note is no longer lost** — core's popup collects a closing
  note and never sends it; the same call stores it on `closing_notes` (which
  the daily sale report already prints) and on the explanatory note of the
  report of differences.
- **Chatter notice** — a session closed out of balance posts the list of the
  methods that did not match, with the amounts.
- **Explanatory note wizard** — `l10n.ro.pos.closing.note` writes the cause
  and the explanation of each line and the note of the session, for what was
  not said at the register or has to be corrected. The session form is read
  only in core, so the wizard is how they are filled in.
- **Report** — `Report of Differences`, a QWeb PDF on `pos.session`: the
  register, the cashier, the control table with the differences first, the
  surplus / shortage / net totals, the note and the signature block. A
  closing whose surpluses cover its shortages is stated as such.
