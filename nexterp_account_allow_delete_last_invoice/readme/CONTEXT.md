# Key features

- **Delete the last posted invoice** in a journal without breaking the accounting sequence lock.
- **Per-company toggle** — enable or disable the behaviour independently for each company via `account_allow_delete_last_invoice` on `res.company`.
- **Standard Settings UI** — the option appears directly in *Settings → Invoicing*, requiring no developer mode or manual configuration.
- **Minimal footprint** — extends only `account.move.unlink` and `res.config.settings`; no new models or data files introduced.
- **Safe by default** — the flag is `False` on installation, so existing companies are unaffected until an administrator explicitly opts in.
