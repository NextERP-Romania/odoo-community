# Configuration

After installing the module, enable the feature per company:

1. Go to **Settings → Invoicing** (or **Settings → Accounting**).
2. Scroll to the **Invoicing** section and locate the **Allow Delete Last Invoice** checkbox (`account_allow_delete_last_invoice`).
3. Tick the checkbox to allow deletion of the last invoice in a journal for the current company.
4. Click **Save**.

Repeat for each company in a multi-company setup that should have this behaviour enabled. Companies where the checkbox is left unticked retain the standard Odoo protection against deleting posted journal entries.
