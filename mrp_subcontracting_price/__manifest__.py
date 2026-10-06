{
    "name": "Purchase Subcontracting Price",
    "version": "20.0.1.0.0",
    "category": "Manufacturing",
    "summary": """
        This module allows calculating the price of subcontracted products
        based on purchase price and the components value
    """,
    "author": "NextERP Romania",
    "website": "https://www.nexterp.ro",
    "license": "OPL-1",
    "images": ["static/description/apps_icon.png"],
    "depends": [
        "l10n_ro_stock_account",
        "mrp_subcontracting_purchase",
    ],
    # Nu se instaleaza pe 20.0: cere `l10n_ro_stock_account`, care inca n-a ajuns pe
    # seria asta in l10n-romania. De reactivat cand apare acolo.
    "installable": False,
    "auto_install": False,
    "application": False,
}
