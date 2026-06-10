# Key features

- **Line-level exception visibility** — `exception_ids`, `exceptions_summary` and `is_exception_danger` are exposed directly on every `purchase.order.line`, not just at order header level.
- **Extends `purchase_exception`** — plugs into the existing OCA exception-rule engine without replacing it; all rules you already configured continue to work unchanged.
- **HTML exception summary** — `exceptions_summary` renders a colour-coded, human-readable digest of all triggered rules per line, visible inline in the order form.
- **Danger flag** — `is_exception_danger` lets you spot critical violations at a glance directly in the order lines list, enabling faster triage on large orders.
- **Zero configuration required** — install and the line-level indicators appear automatically on the standard Purchase Order form.
