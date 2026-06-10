# Configuration

## 1. Company default

1. Go to **Settings → Sales → Quotations & Orders**.
2. Locate the **Auto Create Sale Tasks** setting.
3. Tick it to keep the standard Odoo behaviour (tasks created
   automatically when a sale order with service lines is confirmed).
4. Leave it unticked to switch the company to manual mode — sale
   orders will not generate tasks until the user clicks **Generate
   Tasks** on each order.
5. Click **Save**.

## 2. Per-order override

1. Open any quotation or sale order in **Sales → Orders → Quotations
   / Orders**.
2. Next to the **Payment Terms** field, the **Auto Create Sale
   Tasks** checkbox is shown. It is filled from the company default
   via the `onchange` on **Company**, but you can override it per
   order:
   - **On** — tasks are created automatically on confirmation.
   - **Off** — no tasks are created until **Generate Tasks** is
     clicked.

## 3. Prerequisites

- The module depends on `sale_project`. Make sure the service
  products used on your orders have **Product Type = Service** and
  **Service Tracking = Task in Project** (or *Project & Task*) — the
  standard `_timesheet_service_generation` only acts on these lines.
- The default project on each service product (or on the order)
  must be set so tasks can be created in the right place.

## 4. Access rights

No new access rights are introduced. Standard Sales / Project
groups remain in charge. The **Generate Tasks** button runs through
`sudo()` and `with_company()` so users with Sales access but
limited Project rights can still trigger creation.
