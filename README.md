<!-- /!\ do not modify above this line -->

# odoo-community

odoo-community

[![codecov](https://codecov.io/gh/NextERP-Romania/odoo-community/branch/19.0/graph/badge.svg)](https://codecov.io/gh/NextERP-Romania/odoo-community/branch/19.0)

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[bom_excel_import](bom_excel_import/) | 19.0.1.0.2 |  | This module allows importing Bills of Materials (BOMs) from Excel files. The Excel file should have the following structure: - Column 1: Product produced - Column 2: List of operations in the BOM - Column 3: Quantity consumed in each operation - Column 4: Product/component consumed UOM - Column 5: Product/component consumed - Column 6: Workcenter - Column 7: Subcontracting (boolean) - Column 8: Subcontractors (comma-separated) The import process uses multi step wizard: 1. Import operations and workcenters 2. Import BOMs with the operations The wizard guides you through the complete process in a single interface.
[l10n_ro_edi_extension](l10n_ro_edi_extension/) | 19.0.1.0.3 |  | E-Invoice implementation for Romania
[l10n_ro_edi_stock_batch_extension](l10n_ro_edi_stock_batch_extension/) | 19.0.1.2.0 |  | Brings the l10n_ro_edi_stock_extension facilities to batch transfers
[l10n_ro_edi_stock_extension](l10n_ro_edi_stock_extension/) | 19.0.1.2.0 |  | Fixes and extensions for l10n_ro_edi_stock per ANAF eTransport v2.0.2
[l10n_ro_statement_line_automation](l10n_ro_statement_line_automation/) | 19.0.0.0.0 |  | Automatically create bank statements in statement lines
[mrp_subcontracting_price](mrp_subcontracting_price/) | 19.0.1.0.0 |  | This module allows calculating the price of subcontracted products based on purchase price and the components value
[nexterp_account_allow_delete_last_invoice](nexterp_account_allow_delete_last_invoice/) | 19.0.0.0.1 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Allow Delete Last Invoice
[nexterp_account_analytic_distribution_journal](nexterp_account_analytic_distribution_journal/) | 19.0.1.0.1 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Match analytic distribution models by journal.
[nexterp_account_button_credit_note](nexterp_account_button_credit_note/) | 19.0.1.0.0 |  | NextERP - Hide button Reverse and Create Invoice, form credit note
[nexterp_account_date_in_invoices](nexterp_account_date_in_invoices/) | 19.0.0.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Purchase Invoice Accounting Date
[nexterp_account_edi_journal](nexterp_account_edi_journal/) | 19.0.0.0.0 |  | NextERP - Account EDI Journal
[nexterp_account_invoice_debt_recovery](nexterp_account_invoice_debt_recovery/) | 19.0.0.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Allow Debt Recovery Invoice
[nexterp_account_invoice_report](nexterp_account_invoice_report/) | 19.0.0.0.0 |  | NextERP - Account Invoice Report
[nexterp_account_term_payment_current_month](nexterp_account_term_payment_current_month/) | 19.0.1.0.0 |  | NextERP - Payment Term Current Month
[nexterp_conformity_report](nexterp_conformity_report/) | 19.0.1.0.0 |  | NextERP - Conformity Certificate
[nexterp_delivery_slip_report](nexterp_delivery_slip_report/) | 19.0.0.0.0 |  | NextERP - Stock Delivery Slip Report
[nexterp_inter_company](nexterp_inter_company/) | 19.0.0.0.1 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | This module helps to identify if a record is inter company transaction or not.
[nexterp_inter_company_account](nexterp_inter_company_account/) | 19.0.0.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | This module helps to identify if an account move line and account move is inter company transaction or not.
[nexterp_pos](nexterp_pos/) | 19.0.3.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Keep several sessions open on one register and close them oldest first
[nexterp_product_kit](nexterp_product_kit/) | 19.0.1.0.1 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Product Kit
[nexterp_product_kit_sale](nexterp_product_kit_sale/) | 19.0.1.0.1 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Product Kit Sale
[nexterp_product_kit_sale_timesheet](nexterp_product_kit_sale_timesheet/) | 19.0.1.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Product Kit Sale Timesheet
[nexterp_purchase_exception](nexterp_purchase_exception/) | 19.0.0.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Custom exceptions on purchase order line
[nexterp_sale_task_create](nexterp_sale_task_create/) | 19.0.1.0.1 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Auto Create Sale Tasks
[nexterp_sale_update_price_auto](nexterp_sale_update_price_auto/) | 19.0.1.0.1 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Sale Update Prices Auto
[nexterp_stock_inventory](nexterp_stock_inventory/) | 19.0.1.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Stock Inventory
[nexterp_vehicle_costs](nexterp_vehicle_costs/) | 19.0.1.0.3 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Manage vehicle costs, add categories for fuel and part, etc.

[//]: # (end addons)

<!-- prettier-ignore-end -->
