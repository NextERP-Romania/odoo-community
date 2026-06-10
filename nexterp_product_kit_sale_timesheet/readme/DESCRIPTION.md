Bridge between `nexterp_product_kit_sale` and `sale_project`: when a
sale order is confirmed, one project task is created per kit
component flagged as a service with **Service Tracking = Task in
Project**, in addition to the standard task created for the parent
sale order line.

The hook lives in `sale.order.line._timesheet_create_task`: after
the core task for the parent line is created, the module iterates
over `kit_line_ids` and calls a kit-aware
`_timesheet_create_task` on each component whose product is a
`task_in_project` service. Each kit task is linked back to the
originating `sale.order.line` and nested under the parent task
through the `parent_id` field, so kit hierarchies are visible in the
project's Gantt / hierarchy view.

Targets service-bundle sales where one quotation line resolves to
several billable jobs — installation kits, consulting packages,
multi-stage interventions — and you want each component tracked as
its own task with timesheets attached.
