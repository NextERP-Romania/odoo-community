The question that comes up on every localisation project is "what journal
entries does this operation give me, and how does my stock end up". Until now
the answer came either from a separate test database, or from doing the thing
for real and reversing it afterwards.

The buttons offered are not written into this module. They are read from the
model's own views, form and list alike, so buttons added by other modules
appear as well - and so do the ones Odoo moves around between versions. In
Odoo 20, for instance, "Create Bills" lives in the header of a purchase order
list view rather than on the form.

The idea of running something and then taking it back comes from Marcel
Cojocaru's `database_rollback` module. That one kept a transaction open across
requests, which needs a server with no workers. This one replays the whole
flow inside a single request instead, so it runs anywhere, Odoo.sh included.
