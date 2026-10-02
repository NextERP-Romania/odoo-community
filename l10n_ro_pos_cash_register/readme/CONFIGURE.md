# Configuration

Nothing of its own. Two things have to be true for a session to have a
register at all:

1. **Cash control** on the point of sale (*Point of Sale → Configuration →
   Point of Sale*, the payment section). Without it a session opens no
   `account.bank.statement`, so there is no register — the screen says so on
   the line rather than printing an empty form.
2. **A Romanian company**, since the register form comes from
   `l10n_ro_account_bank_statement_report` and renders the Romanian layout
   for records of a Romanian company.
