# Configuration

After installing `l10n_ro_edi_extension`, complete the following steps.

## 1. Company EDI settings

Go to **Settings → General Settings → Companies** (or **Accounting → Configuration → Settings**) and open your company record.

Set the following fields on the **Romanian EDI** section:

| Field | Description |
|---|---|
| **Period of Residence** (`l10n_ro_edi_residence`) | Fiscal residence period required by ANAF for the EDI exchange. Enter the value as an integer (number of days). |
| **EDI Error Notify Users** (`l10n_ro_edi_error_notify_users`) | Add one or more internal users who should receive an Odoo notification whenever an ANAF submission fails. |

## 2. Review the send-invoices cron

1. Go to **Settings → Technical → Automation → Scheduled Actions**.
2. Find **Romania - Send Invoices to ANAF** (`ir_cron_l10n_ro_send_invoices_anaf`).
3. Adjust the **Execution Frequency** to suit your submission cadence (e.g. every 15 minutes).
4. Ensure the cron is **Active**.

## 3. SPV / ANAF credentials

Ensure the ANAF OAuth credentials are configured as required by the base `l10n_ro_edi` and `l10n_ro_message_spv` modules. This module relies on those credentials to submit outgoing invoices and pull inbound SPV messages.
