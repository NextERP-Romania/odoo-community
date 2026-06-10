# Key features

- New boolean **Auto Create Sale Tasks** on `res.company`, exposed in
  **Settings → Sales → Quotations & Orders**, controlling the default
  behaviour for all sale orders of that company.
- Matching boolean on `sale.order`, initialised from the company
  setting via an `onchange` on `company_id` and shown next to the
  payment terms on the order form.
- Override of `sale.order.line._timesheet_service_generation`:
  - if the context flag `create_tasks=True` is passed, all lines in
    `self` go through the standard generator;
  - otherwise the override filters lines so only those whose order
    has `sale_create_taks_auto=True` trigger task creation.
- New action `sale.order.action_generate_tasks` iterating over
  `order.order_line`, calling `_timesheet_service_generation` with
  `create_tasks=True` only on lines that do not yet have a
  `task_id`; `with_company` is used so multi-company orders keep the
  right project context.
- New **Generate Tasks** button on the sale order form, placed next
  to *Set to Draft*, visible only when **Auto Create Sale Tasks** is
  off — turning the action into a one-click manual fallback.
- All `sudo()` and company switching is handled inside the action so
  salespeople without full project access can still trigger task
  creation on their own orders.
