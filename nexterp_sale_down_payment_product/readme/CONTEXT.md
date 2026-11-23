# Key features

- **Configurable Down Payment Product** — set a company-level `l10n_ro_sale_down_payment_product_id` so every sale order down payment line and its invoice counterpart carry a real product.
- **Fills the Odoo 19 gap** — standard Odoo 19 down payment lines have no product; this module restores product-level tracking without patching core code.
- **Income account fallback** — when no company *Down Payment Account* is configured, the income account is derived from the selected down payment product.
- **Multi-company ready** — the setting is stored per company (`res.company`) and exposed in *Settings → Default Accounts* for each entity.
- **Zero workflow change** — the standard *Create Invoice → Down Payment* flow is unchanged; the product is injected automatically behind the scenes.
