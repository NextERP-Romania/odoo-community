# Configuration

The module has no settings of its own. Configuration consists of
preparing the products that should generate tasks and the project
they will be created in.

## 1. Service products

1. Go to **Sales → Products → Products** (or **Inventory → Products
   → Products**).
2. For every kit component that must become a task, open the product
   and set:
   - **Product Type** — `Service`.
   - **Invoicing Policy** — usually `Based on Timesheets`.
   - **Service Tracking** — `Task in Project` (this is the trigger
     checked by `_timesheet_create_task`).
   - **Project** — the default project where tasks will land (if not
     filled, the parent line's project is reused).
3. Make sure the parent kit product itself is also a
   `task_in_project` service: the override only fires when the
   parent SO line creates a task in the first place.

## 2. Kit definition

1. On the kit product, open the **Kit Products** tab (added by
   `nexterp_product_kit`) and add the service components configured
   at step 1.
2. The non-service components stay in the kit definition without
   producing tasks, so mixed bundles (service + goods) are
   supported.

## 3. Project and timesheets

1. Enable **Project → Configuration → Settings → Timesheets** if not
   already on.
2. Optionally enable **Sub-tasks** so the parent / child hierarchy
   from kit explosion is visible.
3. Grant the relevant users access to the target project.

## 4. Sale workflow

No further configuration is needed in **Sales**. As soon as a kit
service product is added to a quotation and the order is confirmed,
the dependent `nexterp_product_kit_sale` explodes the kit lines and
this module creates one task per service component.
