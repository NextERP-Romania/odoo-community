# Configuration

1. Go to **Settings → Accounting**, section **Romanian E-Factura**.
2. Enable **Send Credit Notes as Invoice 380 with negative values**.

The setting is per company. Accounting entries are not changed: the credit
note stays an `out_refund` in Odoo, only the XML sent to ANAF changes.
