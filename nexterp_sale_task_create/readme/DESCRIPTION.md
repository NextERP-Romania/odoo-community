Switch project-task creation on `sale_project` from always-on to
opt-in. Standard Odoo creates a task as soon as a sale order with a
service product is confirmed; this module gates that behaviour
behind a per-order **Auto Create Sale Tasks** flag (defaulted from
the company setting) and adds a **Generate Tasks** button so users
can trigger the creation manually when the flag is off.

The override lives in `sale.order.line._timesheet_service_generation`:
when the `create_tasks` context key is missing, the standard
generator only runs for SO lines whose order has
`sale_create_taks_auto = True`. The button on the sale order form
calls `action_generate_tasks`, which loops through the order's lines
and runs the generator with `create_tasks=True` for any line that
does not yet have a `task_id`.

Targets project / services businesses where confirming a quotation
should not always spawn tasks — for instance when sales teams
prepare orders ahead of project staffing, or when tasks are created
later from an external planning step.
