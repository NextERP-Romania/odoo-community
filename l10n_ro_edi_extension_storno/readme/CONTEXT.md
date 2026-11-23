# Key features

- **Storno instead of CreditNote** — submits `out_refund` documents to ANAF
  SPV as UBL `Invoice` type **380** with negative values, not CreditNote **381**.
- **Per-company opt-in** — single boolean field `l10n_ro_credit_note_einvoice`;
  companies not enabled keep the default 381 behaviour.
- **Fully negated XML** — line quantities, allowances/charges, VAT totals and
  all `LegalMonetaryTotal` amounts are negated; item net price (BT-146) stays
  positive per BR-27.
- **BillingReference auto-filled** — BT-25 and BT-26 reference the original
  reversed invoice number and date in `cac:BillingReference`.
- **Matching storno PDF** — printed report shows *Storno Invoice* title,
  negative quantities/amounts and a *Storno of invoice …* reference line.
- **Zero accounting impact** — Odoo ledger entries are untouched; only the
  UBL XML sent to e-Factura / SPV changes.
- **UBL compliance** — `DocumentTypeCode 50` suppressed on the embedded PDF
  (not allowed on Invoice 380, per UBL-SR-43).
