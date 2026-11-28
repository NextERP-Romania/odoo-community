1. Set up the e-Factura connection to ANAF (SPV credentials) as required
   by the Romanian e-invoicing localization.
2. Go to **Invoicing > Configuration > Settings**, section **Romanian
   E-Factura**, and fill in:
   - **Period of residence for the e-Invoice after which it is
     automatically sent**: the number of days an invoice waits before it
     is sent automatically (5 by default);
   - **EDI Error Notification Users**: the users notified when a sending
     fails.
3. In developer mode, **Settings > Technical > Automation > Scheduled
   Actions** lists **Romania - Send Invoices to ANAF** (daily) and
   **Romania - Fetch Invoices status from ANAF** (hourly). Adjust their
   frequency if needed and keep them active.
