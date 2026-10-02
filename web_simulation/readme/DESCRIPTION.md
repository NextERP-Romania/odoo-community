Run a document's own buttons without saving anything, and see what they would
do to stock and to the books.

Pick a document, choose one of the buttons it offers - Confirm, Validate,
Post, whatever it has - and the result appears straight away: the documents
that would be created, the stock moves with their values, the resulting stock
on hand, and the journal entries account by account. Then everything is rolled
back and the document is left exactly as it was.

Steps chain across documents. Confirm a purchase order and the receipt it just
created shows up as the next step; validate that and the bill follows. A whole
flow can be put together click by click without a single row surviving it.

The documents the flow creates can be filled in before the next step - set the
received quantity to 3 for a partial receipt, put a date on the bill - and
when Odoo asks a question, such as whether to create a backorder, its dialog
becomes one more step to answer.

A document that was never saved can be simulated too: it is created for the
run only, so not even a draft is left behind.

Nothing is written to the database and no email is sent. It works on any
server, whatever its number of workers.
