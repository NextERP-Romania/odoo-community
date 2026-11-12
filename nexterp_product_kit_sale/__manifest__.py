# Copyright (C) 2022 NextERP Romania SRL
# License OPL-1.0 or later
# (https://www.odoo.com/documentation/user/19.0/legal/licenses/licenses.html#).

{
    "name": "NextERP - Product Kit Sale",
    "summary": "NextERP - Product Kit Sale",
    "version": "19.0.1.3.0",
    "category": "Sales",
    # `sale.order.line.kit` e o copie prototip a lui `sale.order.line`
    # (vezi models/sale_order_kit.py): are tabela lui, cu o coloana pentru
    # fiecare camp stocat al parintelui. Coloanele se creeaza cand se
    # instaleaza modulul asta, deci un modul care adauga un camp stocat pe
    # `sale.order.line` si se incarca dupa noi nu mai ajunge in tabela
    # noastra -- iar la rulare modelul il are (registry-ul se reconstruieste
    # cu toate clasele) si scrierea pica pe o coloana inexistenta.
    # `sale_service` aduce asa `is_service`, iar `sale_project` aduce
    # `project_id`, `task_id` si `reached_milestones_ids`; le cerem explicit,
    # ca sa se incarce inaintea noastra. Nu e de ajuns ca ele sa fie
    # instalate in baza: tabela copilului primeste doar campurile cunoscute
    # cand se incarca modulul asta, si `sale_project` se auto-instaleaza
    # langa Project, deci de obicei vine dupa noi.
    "depends": ["nexterp_product_kit", "sale", "sale_service", "sale_project"],
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "support": "odoo_apps@nexterp.ro",
    "data": [
        # views
        "views/sale_order_views.xml",
        # security
        "security/ir.model.access.csv",
    ],
    "installable": True,
    "auto_install": False,
    "development_status": "Mature",
    "maintainers": ["feketemihai"],
    "images": ["static/description/apps_icon.png"],
    "license": "OPL-1",
}
