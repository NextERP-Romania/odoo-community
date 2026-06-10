# Configuration

The report is registered as `ir.actions.report` with
`binding_model_id = stock.picking`, so no specific configuration menu
is exposed. After installing the module, the **Conformity Report**
entry appears automatically under the **Print** menu of every transfer
form.

## 1. Company information

The declaration paragraph at the bottom of the PDF reads the issuing
company partner. Make sure the following fields are filled, otherwise
the corresponding parts of the sentence will print blank:

1. Go to **Settings -> Companies -> Companies** (or
   **Settings -> Users & Companies -> Companies**).
2. Open the company and verify:
   - **Name** — printed at the start of the declaration.
   - **City** and **Street** — printed in the company address part of
     the declaration.

## 2. Romanian localization fields (optional but recommended)

The template reads several optional Romanian-localization fields if
they exist on the picking and partner. Filling them improves the
output:

| Field | Source | Used for |
|---|---|---|
| `l10n_ro_accounting_date` | `stock.picking` | Dispatch date in the header and declaration |
| `l10n_ro_delegate_id` | `stock.picking` | Name of the delegate in the signature block |
| `l10n_ro_mean_transp` | `stock.picking` | Means of transport in the signature block |
| `nrc` | `res.partner` | Trade register number under the customer address |
| `vat` | `res.partner` | VAT / Tax ID under the customer address |

## 3. Lot tracking

Quantities are listed from `move_line_ids`. For the **Lot No.** and
**Minimum shelf life** columns to be populated, the products must be
tracked by lot and the corresponding `stock.lot` records must carry an
`expiration_date`.
