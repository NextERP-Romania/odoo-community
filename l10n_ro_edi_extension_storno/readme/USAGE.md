# Usage

## Sending a credit note to ANAF as a storno invoice

Once the company setting is enabled (see Configuration), the storno behaviour
applies automatically every time you send a customer credit note to ANAF
e-Factura / SPV.

1. Create a customer credit note as usual (*Accounting → Customers →
   Credit Notes → New*), or use **Add Credit Note** on a posted invoice to
   reverse it.
2. Fill in the credit note lines and confirm (post) the document. The move
   type remains `out_refund` in Odoo — accounting entries are unchanged.
3. Click **Send & Print** (or the e-Factura send action). Instead of a
   `CreditNote` UBL document with `InvoiceTypeCode` **381**, the XML
   transmitted to ANAF SPV is an `Invoice` with `InvoiceTypeCode` **380**
   and all amounts/quantities negated.
4. The embedded PDF printed alongside the XML also reflects the storno
   format: title reads *Storno Invoice*, dates are labelled *Invoice Date*,
   and a *Storno of invoice … dated …* reference line is included. Line
   quantities and amounts are negative; unit prices remain positive
   (BT-146, as required by BR-27).
5. The original reversed invoice is referenced automatically in
   `cac:BillingReference` (BT-25 number and BT-26 issue date), so ANAF
   can link the storno to the source document.

> **Note:** Companies that do **not** have `l10n_ro_credit_note_einvoice`
> enabled continue to submit standard 381 CreditNote documents — no change
> in their workflow.
