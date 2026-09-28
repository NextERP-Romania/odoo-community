# Usage

## Pinning an Analytic Distribution Model to a Journal

1. Go to **Accounting → Configuration → Analytic Distribution Models**.
2. Open an existing model or click **New** to create one.
3. In the **Journal** field, select the journal (e.g. *Customer Invoices*, *Vendor Bills*, *Bank*) to which this model should be restricted.
4. Save the record.

From this point on, when Odoo auto-applies analytic distributions to journal items (`account.move.line`), the model will only match lines that belong to the selected journal. Lines posted in any other journal will skip this model entirely.

## Leaving a Model Journal-agnostic

If the **Journal** field is left empty, the model behaves exactly as in standard Odoo — it is applied to journal items from **all** journals, just as before installation of this module.

## Typical scenario

You have two cost centres and want:
- *Project costs* analytic plan → applied only to lines in the **Vendor Bills** journal.
- *Operating expenses* analytic plan → applied to every other journal.

Steps:
1. Open the *Project costs* distribution model and set **Journal** = `Vendor Bills`.
2. Leave the *Operating expenses* model's **Journal** field blank.
3. Post a vendor bill — only the *Project costs* model fires.
4. Post a bank payment — only the *Operating expenses* model fires.
