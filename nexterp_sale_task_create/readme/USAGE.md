# Daily use

## Automatic mode

When **Auto Create Sale Tasks** is ticked (either at company level
or on the specific order), the behaviour matches stock Odoo:

1. The user confirms a sale order containing service lines flagged
   as **Task in Project**.
2. `_timesheet_service_generation` runs as usual and creates one
   task per qualifying SO line.
3. The **Generate Tasks** button is hidden — there is nothing to
   trigger manually.

## Manual mode

When the flag is off (company default or per-order override):

1. The user confirms the sale order. No tasks are created — the
   override on `_timesheet_service_generation` filters the order
   out because `sale_create_taks_auto` is False on the order.
2. The **Generate Tasks** button (red primary button next to *Set
   to Draft*) becomes visible. The user clicks it whenever the
   tasks should actually exist (after staffing decisions, billing
   confirmation, kick-off meeting, etc.).
3. `action_generate_tasks` iterates over `order.order_line` and,
   for every line that does not already have a `task_id`, calls
   `_timesheet_service_generation` with the `create_tasks=True`
   context. This forces the override to bypass the filter and
   create the task.
4. The button is safe to click multiple times: lines that already
   have a `task_id` are skipped, so it can also be used to catch up
   on later additions to the order.

## Mixed orders

The flag applies to the whole sale order, but the standard
generator already filters out non-service lines and lines that do
not require a task. Mixed orders (services + goods) only generate
tasks for the service lines, just like the original behaviour.

## Switching mode mid-flight

- Changing the company default does not retroactively update
  existing orders; the value is copied to each order at creation
  through the `onchange`. To enable / disable for an existing
  order, edit the **Auto Create Sale Tasks** field directly on the
  order form.
- Switching from manual to automatic on an existing order does not
  re-fire `_timesheet_service_generation`. Click **Generate Tasks**
  (or temporarily switch the order to manual and click) to create
  the missing tasks.
