# Usage

## Marking an Invoice for Debt Recovery

1. Go to **Invoicing → Customers → Invoices** and open the overdue invoice you want to send to debt recovery.
2. Click the **Mark as Debt Recovery** server action (available from the action menu or the form button).
   - The `debt_recovery` flag is set to `True` on the `account.move` record.
   - The `payment_state` is updated to reflect *Debt Collector* status, blocking the receivable line from further follow-up sequences.
3. Switch to the **Debt Recovery** tab on the invoice form to fill in the case details:
   - **Debt Status** (`debt_state`) — choose `Notification` (first contact) or `Lawyer` (escalated).
   - **Debt Case Date** (`debt_case_date`) — the date the case was opened.
   - **Law Reference** (`debt_law`) — optional legal act or case number.
   - **Debt Amount** (`debt_amount`), **Commission** (`debt_commission`), **Penalties** (`debt_penalties`) — monetary breakdowns tracked separately from the original invoice amount.
   - **Debt Recovery Text** (`debt_recovery_text`) — free-text field for terms, notes or correspondence history.
4. Save the record. The invoice list view now shows the debt recovery status, and the search panel includes a **Debt Recovery** filter for quick reporting.

## Marking a Debt as Resolved

1. Once the invoice is paid or the debt is settled, open the invoice.
2. Tick **Debt Recovery Done** (`debt_recovery_done`) on the Debt Recovery tab.
3. The `payment_state` recomputes normally and the receivable line is unblocked.
