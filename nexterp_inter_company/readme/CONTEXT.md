# Key features

- **`is_inter_company` computed field** — automatically flags any record as an inter-company transaction by inspecting `company_id` and `partner_id` fields against the companies registered in your Odoo database.
- **Reusable mixin** — `base.inter.company` can be inherited by any model that needs inter-company detection, without additional coding.
- **Partner-level detection** — `res.partner` is extended with a stored computed `is_inter_company` field, making it easy to filter or group partners that represent sister companies.
- **No configuration required** — works out of the box based on the companies already defined in your system.
- **Lightweight dependency** — depends only on `base`, so it can be safely added to any Odoo instance regardless of installed apps.
- **Foundation for reporting** — designed to let companion modules and custom reports exclude or isolate inter-company lines from external business figures.
