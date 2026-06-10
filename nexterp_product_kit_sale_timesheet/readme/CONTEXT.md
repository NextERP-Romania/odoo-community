# Key features

- Override of `sale.order.line._timesheet_create_task`: after the
  standard task is created for a `task_in_project` parent line, the
  module loops over its `kit_line_ids` and creates one extra task per
  service component.
- Component-level task creation only fires when the kit component
  product also has `service_tracking == "task_in_project"`, so mixed
  kits (services + storable) generate tasks only where it makes
  sense.
- New `sale.order.line.kit._timesheet_create_task` builds the task
  itself: it prepares values via
  `_timesheet_create_task_prepare_values`, creates the task with
  `sudo()` and writes its id back onto the kit line through
  `task_id`.
- Task naming convention:
  `"<Order name>: <parent product> - <component product>"` — gives
  immediate context in project lists, Kanban and search.
- Tasks are linked back to the originating `sale.order.line` via
  `sale_line_id` (so timesheet billing stays attached to the parent
  SO line) and nested under the parent task via `parent_id`, using
  the `parent_task` context key passed by the override.
- Override of `sale.order._compute_tasks_ids`: when computing the
  set of tasks belonging to an order, kit-line tasks that are not
  yet linked to a `sale_line_id` are re-attached to their parent SO
  line, keeping the order's task list consistent.
- A creation message is posted on each kit task with a clickable
  link back to the source sale order.
