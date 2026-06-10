# How it works

The whole module is one override on `account.bank.statement.line.create`.
There is nothing to click — usage is observing the side effect when
new lines are created.

## Trigger

A new `account.bank.statement.line` is created (single record or batch)
on a company whose country is `RO`, and `statement_id` is not set in
the `vals`.

## Resolution

For each affected line, the override:

1. Searches `account.bank.statement` for a record with
   `journal_id == record.journal_id` and `date == record.date`.
2. If a statement exists, links the line to it.
3. If no statement exists, creates one with `journal_id`, `date`, and
   `name = date`, then links the line to the new statement.
4. Calls `_compute_balance_end` and `_compute_balance_end_real` on the
   resulting statement so the closing balance is refreshed
   immediately.

## Typical flow

1. A bank-statement importer (CAMT.053, MT940, custom feed) calls
   `create()` on `account.bank.statement.line` with one record per
   transaction.
2. Odoo would normally leave each line orphaned until a user opens
   **Accounting → Bank → Bank Statements** and creates a daily
   statement.
3. With this module installed, the line is already attached to a
   per-journal, per-date statement by the time `create()` returns.
4. Open **Accounting → Bank** to find the statement listed with its
   computed end balance; the lines are visible inside it.

## What it does not do

- Does not reconcile or match the line to a journal entry.
- Does not change the line's amount, partner or labels.
- Does not run on non-Romanian companies, even in a multi-company
  database.
- Does not create statements for lines that already have a
  `statement_id`.
