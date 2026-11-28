1. Set up eTransport and the ANAF connection as required by the Romanian
   eTransport localization.
2. Go to **Invoicing > Configuration > Settings**, section **Romanian
   E-Factura**, block **eTransport additional settings**:
   - **Default eTransport Price Source**: where the values without VAT
     come from; *Automatic (by operation)* suits most companies;
   - **Delivery Carrier Required**: *When the notification is sent* (the
     default) lets transfers be validated without a carrier and asks for
     it when the notification goes to ANAF; *When the transfer is
     validated* asks for it on every receipt and delivery. Either way the
     carrier needs an eTransport partner with VAT number, city and street;
   - **Automatic List Sync**: tick it to match the ANAF notifications list
     with the transfers every six hours;
   - **List Sync Days**: how many days back each synchronization looks
     (1 to 60).
3. Make sure every product moved under eTransport has its customs tariff
   code (4, 6 or 8 digits) on the product form.
4. Write partner addresses as *street name and number* (for instance
   *Calea Victoriei 12-14*), so the street and the number are split
   correctly.
5. Optionally, in developer mode, activate the scheduled action
   **eTransport: fetch ANAF status of transfers** in **Settings >
   Technical > Automation > Scheduled Actions**, to fetch the answers to
   deletions, confirmations and vehicle changes automatically.
