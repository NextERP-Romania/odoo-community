# Romania - E-invoicing Extension

Extends the standard Odoo Romanian e-invoicing stack (`l10n_ro_edi`) with production-grade reliability improvements for the **e-Factura / SPV** workflow: automated cron-driven sending, inbound bill ingestion from the SPV portal, UBL XML compliance fixes, and company-level error notifications.

Romanian regulations require that VAT-registered companies submit outgoing invoices to ANAF's SPV (Spațiul Privat Virtual) as UBL XML and also receive supplier invoices through the same portal. This module closes the gaps left by the base localization module:

## What this module provides

- **Automated invoice submission cron** (`ir_cron_l10n_ro_send_invoices_anaf`) — periodically picks up invoices that are ready to send and submits them to ANAF without manual intervention.
- **SPV bill ingestion** — `_l10n_ro_edi_fetch_invoices` and `_l10n_ro_edi_process_bill_messages` synchronize supplier bills received in the SPV and create the corresponding `account.move` records in Odoo if they do not already exist.
- **UBL XML length-limit enforcement** — `_ro_apply_length_limits`, `_ro_truncate`, `_ro_truncate_text`, and `split_string` on `account.edi.xml.ubl_ro` ensure that free-text fields (item names, descriptions, notes) never exceed the character limits mandated by the CIUS-RO specification, preventing ANAF rejections.
- **Invoice line note nodes** — `_add_invoice_line_note_nodes` and `_ubl_add_line_item_name_description_nodes` improve the completeness of generated UBL XML for invoices with long descriptions.
- **Period of Residence setting** (`l10n_ro_edi_residence` on `res.company`) — configures the fiscal residence period used in the EDI exchange.
- **EDI error notifications** (`l10n_ro_edi_error_notify_users` on `res.company`) — designates specific Odoo users who receive internal messages whenever an EDI submission error occurs, so failures are never silently dropped.
- **Send & print shortcut** (`action_send_and_print_anaf`) — a dedicated button on the invoice form that triggers ANAF submission and PDF generation in one step.
- **Default sending method hook** — `_get_default_sending_methods` ensures the Romanian EDI channel is pre-selected when sending invoices, and `_hook_invoice_document_before_pdf_report_render` aligns PDF generation with EDI dispatch.
