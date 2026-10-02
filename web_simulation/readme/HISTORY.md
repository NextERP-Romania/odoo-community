## 20.0.1.0.0

- First version: chain a document's buttons, see what each step would produce
  on stock and on the books, and roll it all back.
- The buttons offered are read from the model's views, not written into the
  module.
- Documents and their lines can be filled in between steps, which is what
  makes a partial receipt or a dated bill possible. One column, and each row
  edited with the widget of its own type, links included.
- Dialogs Odoo opens to ask something - create the backorder? - are answered
  with their own buttons.
- Unsaved documents can be simulated as well.
- Document numbers are not consumed by a simulation.
