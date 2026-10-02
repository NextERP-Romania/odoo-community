# Daily use

The cashier closes the session as before, declaring what is in hand for each
payment method. What is new is one question asked at that moment, for the
methods that do not match, and a document that can be printed afterwards.

## 1. Explain the difference at the register

As soon as a counted amount differs from what the register recorded, the
closing popup shows a **Differences found** section under the counts, with
one line per payment method that did not match:

- the method and the difference, so there is no doubt which one is meant;
- a **cause**: *Takings recorded on another payment method*, *Counting error
  at closing*, *Takings missing*, *Surplus without a known origin* or
  *Other*;
- an **explanation** in free text, printed as typed on the report.

The **Closing note** of the same popup is the note of the whole closing, and
it is printed at the end of the report. Until now Odoo collected it and threw
it away on the way to the server; it is now kept, both for this report and
for the daily sale report that already printed it.

Nothing is mandatory: a cashier in a hurry closes as before, and the back
office completes what is missing at step 3.

## 2. See that a session did not match

Open **Point of Sale → Orders → Sessions** and pick the closed session. A
session with differences carries:

- a chatter message listing the payment methods that did not match and by how
  much, posted when the session closed;
- a **Closing Differences** tab with one line per controlled payment method:
  **Recorded**, **Counted** and **Difference**, the lines in red being the
  ones that did not match;
- the **Surplus**, **Shortage** and **Net difference** totals of the session.

A difference is read as counted less recorded: a positive amount is money in
hand above what the register knows about, a negative one money missing from
it.

## 3. Complete or correct the explanation

Click **Explanatory Note** in the header. The wizard lists the same lines,
already carrying what was typed at the register, with two columns to fill
in:

- **Cause** — one of *Takings recorded on another payment method*, *Counting
  error at closing*, *Takings missing*, *Surplus without a known origin* or
  *Other*.
- **Explanation** — the sentence printed on the report, for instance: *the
  order of 120 lei was cashed in on the card method while the money was taken
  in cash*.

Below them, the **Explanatory Note** of the session covers the closing as a
whole. **Save** keeps everything on the session; **Save and Print** goes
straight to the report.

## 4. Print the report of differences

**Report of Differences**, in the header of the session or in its **Print**
menu, renders the PDF: the register and the cashier, the opening and closing
times, the control table with the differences first, the totals, the causes
and explanations, the note, and the signature block for the cashier, the shop
manager and the accountant.

When the surpluses cover the shortages to the last leu, the report states it:
the takings of the session are complete, and the differences are only amounts
recorded on a payment method other than the one the money came in on. That is
the paragraph the file needs for a card payment that was in fact cash.

## 5. What is not covered

The accounting of the differences is core's: the gap of a bank method is
posted to the profit or loss account of its journal, the gap of the cash
method is a correction line on the cash statement. The report explains those
entries, it does not replace them, and it does not move an amount from one
payment method to another.

Sessions closed before the module was installed carry no control lines;
printing their report says so instead of printing an empty one.
