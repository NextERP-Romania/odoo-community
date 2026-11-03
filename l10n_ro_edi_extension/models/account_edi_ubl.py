from odoo import models


class AccountEdiXmlUBLRO(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_ro"

    # ------------------------------------------------------------------
    # Tree helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _ro_iter_children(parent, key):
        if not isinstance(parent, dict):
            return
        value = parent.get(key)
        if value is None:
            return
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    yield item
        elif isinstance(value, dict):
            yield value

    # ------------------------------------------------------------------
    # Header / line builders
    # ------------------------------------------------------------------

    def _ubl_add_line_item_name_description_nodes(self, vals):
        item_node = vals["item_node"]
        base_line = vals["line_vals"]["base_line"]
        product = base_line["product_id"]

        if base_line.get("_removed_tax_data"):
            name = description = base_line["_removed_tax_data"]["tax"].name
        else:
            name = product.name or ""
            if line_name := base_line.get("name"):
                description = line_name
                if not name:
                    name = line_name
            else:
                description = product.description_sale or ""

        # BT-154 / BT-153 — lengths are enforced by l10n_ro_edi_extension_limits.
        item_node["cbc:Description"] = {"_text": description} if description else None
        item_node["cbc:Name"] = {"_text": name} if name else None
