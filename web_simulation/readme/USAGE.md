On any document, open the actions menu (the cog) and choose **Simulate**.

A window lists the buttons the document offers, with a column saying which of
them apply right now. Pick one. The flow runs, and you see both the result so
far and what could come next.

Steps chain across documents:

1. on a purchase order, add *Confirm Order*;
2. the receipt it created appears in the list - add *Validate*;
3. the order now offers *Create Bills* - add it;
4. the bill that appeared offers *Post*.

**Undo Last Step** drops the last step, **Start Over** empties the flow.

## Filling documents in

The documents the flow creates cannot be opened, because they only exist
while the flow is being replayed. What can be done instead is fill them in:
**Fill in a document** lists everything the flow touched - the order, the
receipt, the bill, and the lines under them - and *Fill In* shows that
record's fields with their current values. There is one *New Value* column,
and each row is edited with the widget of its own type: a quantity as a
number, an amount with its currency, a date in a date picker, a link with a
record picker that only offers records of the right model. Tick *Change* on
what the flow should set. It becomes a step like any other, applied just before the next button
on every replay.

A list of records - the taxes on an invoice line, for instance - is changed
one record at a time: pick it and say whether to *Add* it, *Remove* it, or
keep *Only this* one. Ticking *Change* without picking anything empties the
list.

That is how a partial receipt is tried out: set *Quantity* to 3 on the
receipt's move line, then validate. And how a bill gets posted: set its
*Invoice/Bill Date* first.

## Answering what Odoo asks

Some buttons ask a question before doing the work - whether to create a
backorder, which lots to take. The dialog that would have opened is treated
as one more record: its own buttons appear at the top of *What can come
next*, and picking one carries the flow on. A partial receipt followed by
*Create Backorder* produces both the receipt and the backorder.

## What you get back

- **Documents** - everything created or changed, with its status and amount;
- **Stock Moves** - the moves that completed, with quantity and value;
- **Stock On Hand** - how stock ends up, per product, location and lot;
- **Accounting By Account** - the totals per account, with the debit and
  credit totals and a check that the entries balance;
- **Journal Items** - the lines themselves, per entry.

## What it will not do

The flow is replayed from scratch every time a step is added, and rolled back
at the end, so the document it starts from is never modified. A document that
is not saved yet is created for the run only.

A step that Odoo refuses - a missing date, a lot that has to be given - stops
the flow there. The step is marked in red with the reason, and the result of
the earlier steps stays on screen. Fill the record in and the step goes
through.

Only fields can be set, not lines: a document's lines cannot be added or
removed from here, only the values on the lines the flow produced.
