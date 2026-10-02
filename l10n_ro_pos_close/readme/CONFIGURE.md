# Configuration

The module ships with no settings page: it starts working at the first
session closed after it is installed.

## Access rights

- **Point of Sale / User** reads and writes the closing control lines, so a
  cashier can state the cause of their own differences, and can open the
  explanatory note wizard.
- **Point of Sale / Administrator** can also delete them.

The lines are restricted to the companies of the user by a record rule on
`company_id`, which follows the company of the session.

## Payment methods

Only the payment methods of the register that are of type **Cash** or **Bank**
are controlled. A method of type **Customer Account** (pay later) is not
counted at closing and is left out of the report.

If a register has more than one bank method — a card terminal and a meal
voucher method, say — each is controlled separately, which is what makes a
payment recorded on the wrong one visible.
