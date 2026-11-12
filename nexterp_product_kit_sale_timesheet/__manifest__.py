# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Product Kit Sale Timesheet",
    "summary": "NextERP - Product Kit Sale Timesheet",
    "version": "19.0.1.1.0",
    "category": "Sales",
    "depends": ["sale_project", "nexterp_product_kit_sale"],
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "installable": True,
    # Puntea extinde `sale.order.line.kit` si vine dupa `sale_project`, deci
    # instalarea ei e si momentul in care tabela kitului primeste coloanele
    # aduse de `sale_project` (project_id, task_id, reached_milestones_ids).
    # Lasata optionala, o baza cu Project si kituri ramane fara ele.
    "auto_install": True,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "images": ["static/description/apps_icon.png"],
    "license": "OPL-1",
}
