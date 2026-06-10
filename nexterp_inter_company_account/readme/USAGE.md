# Usage

## Filtering inter-company journal entries

### Identifying inter-company invoices

1. Open **Accounting → Customers → Invoices** (or **Vendors → Bills**).
2. In the search bar, use the **Inter Company** filter that this module adds (`view_account_invoice_filter_inter_company`) to display only moves where `is_inter_company = True`.
3. Inspect each invoice — the `is_inter_company` flag is computed and stored directly on `account.move`, so it is available for grouping and reporting without additional configuration.

### Filtering journal entries

1. Open **Accounting → Accounting → Journal Entries**.
2. Use the **Inter Company** search filter (`view_account_move_filter_inter_company`) to narrow entries to inter-company transactions.

### Filtering journal items

1. Open **Accounting → Accounting → Journal Items**.
2. Use the **Inter Company** filter (`view_account_move_line_filter_inter_company`) available on `account.move.line`. The field `is_inter_company` is related from the parent move, so every line inherits the flag automatically.

### Invoice analysis report

1. Open **Accounting → Reporting → Invoice Analysis**.
2. Use the **Inter Company** search facet (`view_account_invoice_report_search_inter_company`) to segment analytics by inter-company vs. third-party volumes.
