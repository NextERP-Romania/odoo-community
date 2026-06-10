# Configuration

The module is dependency-driven: install it and the automation runs as
soon as a Romanian company creates a bank statement line. There are no
settings, no menus and no user-facing toggles.

## 1. Install dependencies

The manifest depends on:

- `account` — bank statement and statement line models.
- `l10n_ro` — Romanian localisation; required so the country detection
  on `res.company` matches a real installed chart.

Both must be installable in the database before this module.

## 2. Set the company country

Go to **Settings → Companies → Companies** and open the Romanian
company. Make sure **Country** is set to **Romania** (`RO`). The
automation reads `record.company_id.country_id.code` to decide whether
to run, so any company with a different country code is skipped.

## 3. Configure a bank journal

Go to **Accounting → Configuration → Journals** and ensure each bank
journal that receives lines has the right currency and accounting
defaults. The module does not create journals; it only attaches lines
to statements within an existing journal.

## 4. Optional — import pipelines

The automation is most useful when statement lines arrive without a
parent statement, for example:

- **CAMT.053 / MT940 imports** via `account_bank_statement_import_*`
  modules that read one transaction per line.
- **OCR uploads** through `account_invoice_extract` or a custom
  connector that drops lines into a journal.
- **External connectors** posting `account.bank.statement.line`
  records via XML-RPC / `web` API.

No specific setup is required on these pipelines — once they create
the lines, this module fills in `statement_id`.

## 5. User access

The override runs in `sudo`-less context as the user who creates the
line. Standard Accounting access on
`account.bank.statement` / `account.bank.statement.line` is enough; no
extra security groups are added.
