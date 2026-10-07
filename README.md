<!-- /!\ do not modify above this line -->

# odoo-community

odoo-community

[![codecov](https://codecov.io/gh/NextERP-Romania/odoo-community/branch/20.0/graph/badge.svg)](https://codecov.io/gh/NextERP-Romania/odoo-community/branch/20.0)

<!-- /!\ do not modify below this line -->

<!-- prettier-ignore-start -->

[//]: # (addons)

Available addons
----------------
addon | version | maintainers | summary
--- | --- | --- | ---
[bom_excel_import](bom_excel_import/) | 20.0.1.0.1 |  | This module allows importing Bills of Materials (BOMs) from Excel files. The Excel file should have the following structure: - Column 1: Product produced - Column 2: List of operations in the BOM - Column 3: Quantity consumed in each operation - Column 4: Product/component consumed UOM - Column 5: Product/component consumed - Column 6: Workcenter - Column 7: Subcontracting (boolean) - Column 8: Subcontractors (comma-separated) The import process uses multi step wizard: 1. Import operations and workcenters 2. Import BOMs with the operations The wizard guides you through the complete process in a single interface.
[l10n_ro_edi_stock_extension](l10n_ro_edi_stock_extension/) | 20.0.1.4.0 |  | Fixes and extensions for l10n_ro_edi_stock per ANAF eTransport v2.0.2, on transfers and batch transfers
[l10n_ro_pos_close](l10n_ro_pos_close/) | 20.0.1.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Record the differences per payment method at the closing of a POS session and print the report that explains them
[l10n_ro_statement_line_automation](l10n_ro_statement_line_automation/) | 20.0.0.0.0 |  | Automatically create bank statements in statement lines
[nexterp_account_allow_delete_last_invoice](nexterp_account_allow_delete_last_invoice/) | 20.0.0.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Allow Delete Last Invoice
[nexterp_account_date_in_invoices](nexterp_account_date_in_invoices/) | 20.0.0.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Purchase Invoice Accounting Date
[nexterp_account_edi_journal](nexterp_account_edi_journal/) | 20.0.0.0.0 |  | NextERP - Account EDI Journal
[nexterp_account_invoice_debt_recovery](nexterp_account_invoice_debt_recovery/) | 20.0.0.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Allow Debt Recovery Invoice
[nexterp_account_invoice_report](nexterp_account_invoice_report/) | 20.0.0.0.0 |  | NextERP - Account Invoice Report
[nexterp_delivery_slip_report](nexterp_delivery_slip_report/) | 20.0.0.0.0 |  | NextERP - Stock Delivery Slip Report
[nexterp_inter_company](nexterp_inter_company/) | 20.0.0.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | This module helps to identify if a record is inter company transaction or not.
[nexterp_inter_company_account](nexterp_inter_company_account/) | 20.0.0.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | This module helps to identify if an account move line and account move is inter company transaction or not.
[nexterp_pos](nexterp_pos/) | 20.0.3.0.1 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Keep several sessions open on one register and close them oldest first
[nexterp_product_kit](nexterp_product_kit/) | 20.0.1.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Product Kit
[nexterp_product_kit_sale](nexterp_product_kit_sale/) | 20.0.1.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Product Kit Sale
[nexterp_product_kit_sale_timesheet](nexterp_product_kit_sale_timesheet/) | 20.0.1.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Product Kit Sale Timesheet
[nexterp_sale_task_create](nexterp_sale_task_create/) | 20.0.1.0.1 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Auto Create Sale Tasks
[nexterp_sale_update_price_auto](nexterp_sale_update_price_auto/) | 20.0.1.0.1 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | NextERP - Sale Update Prices Auto
[nexterp_stock_inventory](nexterp_stock_inventory/) | 20.0.1.1.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Stock Inventory
[web_simulation](web_simulation/) | 20.0.1.0.0 | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Run a document's buttons without saving, and see what they would do to stock and to the books


Unported addons
---------------
addon | version | maintainers | summary
--- | --- | --- | ---
[l10n_ro_edi_extension](l10n_ro_edi_extension/) | 20.0.1.0.2 (unported) |  | E-Invoice implementation for Romania
[mrp_subcontracting_price](mrp_subcontracting_price/) | 20.0.1.0.0 (unported) |  | This module allows calculating the price of subcontracted products based on purchase price and the components value
[nexterp_conformity_report](nexterp_conformity_report/) | 20.0.1.0.0 (unported) |  | NextERP - Conformity Certificate
[nexterp_purchase_exception](nexterp_purchase_exception/) | 20.0.0.0.0 (unported) | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Custom exceptions on purchase order line
[nexterp_stock_inventory_retail](nexterp_stock_inventory_retail/) | 20.0.1.0.0 (unported) | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Markup and deferred VAT on the inventory report
[nexterp_vehicle_costs](nexterp_vehicle_costs/) | 20.0.1.0.1 (unported) | <a href='https://github.com/feketemihai'><img src='https://github.com/feketemihai.png' width='32' height='32' style='border-radius:50%;' alt='feketemihai'/></a> | Manage vehicle costs, add categories for fuel and part, etc.

[//]: # (end addons)

<!-- prettier-ignore-end -->
