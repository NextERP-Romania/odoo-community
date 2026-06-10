# Daily use

## What happens on order confirmation

1. The user confirms a sale order that contains a kit service
   product (parent SO line with `service_tracking == "task_in_project"`).
2. Standard `sale_project` creates the task for the parent SO line.
3. This module then loops over `kit_line_ids` on that SO line and,
   for every component whose own product is also `task_in_project`:
   - creates a new `project.task` via `sale.order.line.kit._timesheet_create_task`;
   - writes the task id onto the kit line (`task_id`);
   - attaches it to the parent SO line through `sale_line_id`;
   - sets `parent_id` to the task created at step 2, so the kit
     task appears as a sub-task in the project.
4. The new task gets the name
   `"<Order>: <parent product> - <component product>"` and receives a
   chatter message pointing back to the source order.

## Tracking the tasks

- Open **Project → All Tasks** and filter / group by the sale order
  to see the parent task and its kit sub-tasks together.
- The **Tasks** smart button on the sale order shows the same set;
  `_compute_tasks_ids` is overridden so kit tasks created before the
  order's full reload are still reattached to the parent SO line.
- Open any kit task to view the chatter link back to the originating
  sale order.

## Time tracking and invoicing

- Time logged on a kit task is recorded against its
  `sale_line_id` — the parent SO line of the kit. Invoicing the
  parent line therefore aggregates the timesheets of every kit
  sub-task plus its own.
- This matches the kit pricing model used by
  `nexterp_product_kit_sale`: the customer sees and pays one SO line
  while internally the work is split across multiple tasks.

## Caveats

- Kit components that are not services (or services not flagged as
  `task_in_project`) are silently skipped — no task is created for
  them.
- The override does not delete tasks when a kit line is removed
  later. If you re-explode a kit, expect orphan tasks unless they
  are archived manually.
