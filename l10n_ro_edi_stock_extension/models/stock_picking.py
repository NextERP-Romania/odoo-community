# Copyright 2026 NextERP Romania SRL
import logging
import re

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

from .etransport_constants import (
    EU_COUNTRY_CODES,
    OPERATION_TYPE_TO_ALLOWED_SCOPE_CODES_FULL,
    VALID_COUNTRY_CODE_MAP,
    is_national,
    is_outgoing,
    needs_goods_full_data,
)
from .l10n_ro_edi_stock_document import EXTRA_DOCUMENT_STATES

_logger = logging.getLogger(__name__)


# Pattern for extracting the street number from the "street" field
# (Odoo stores street name and number together).
_STREET_NUMBER_PATTERN = re.compile(
    r"^(.*?[A-Za-zĂÂÎȘȚăâîșț\.\s])\s*(\d+[A-Za-z]?(?:[-/]\d+[A-Za-z]?)?)\s*(.*)$"
)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # The base ``l10n_ro_edi_stock_state`` field copies ``document.state`` into a
    # Selection limited to DOCUMENT_STATES. The extension adds extra document
    # states (deleted / confirmed / vehicle modified), so the picking selection
    # has to be widened too, otherwise the state compute raises
    # ``ValueError: Wrong value ... 'stock_vehicle_modified'``.
    l10n_ro_edi_stock_state = fields.Selection(
        selection_add=EXTRA_DOCUMENT_STATES,
        ondelete={k: "set null" for k, _ in EXTRA_DOCUMENT_STATES},
    )

    # Configurable price source per transfer
    l10n_ro_edi_stock_price_source = fields.Selection(
        selection=[
            ("auto", "Automatic (by operation)"),
            ("cost", "Cost price (standard_price)"),
            ("purchase", "Purchase order price"),
            ("sale", "Sale order price"),
            ("list", "Product list price"),
        ],
        default="auto",
        string="eTransport Price Source",
        help="Source for the VAT-excluded value sent to ANAF.\n"
        "Automatic: uses cost price on purchases and internal transfers; "
        "uses sale price on deliveries.",
    )

    # Multiple transport documents
    l10n_ro_edi_stock_document_line_ids = fields.One2many(
        comodel_name="l10n.ro.edi.stock.document.line",
        inverse_name="picking_id",
        string="Transport Documents",
    )

    # Previous notifications for operations 60/70
    l10n_ro_edi_stock_previous_ids = fields.One2many(
        comodel_name="l10n.ro.edi.stock.previous.notification",
        inverse_name="picking_id",
        string="Previous Notifications",
    )

    l10n_ro_edi_stock_post_outage = fields.Boolean(
        string="Post-Outage Declaration",
        help="OUG 41/2022 art. 8 par. 1^3 - declaration allowed until the end "
        "of the next working day after the ANAF system is restored.",
    )

    ################################################################################
    # Stricter validation per ANAF Schematron v2.0.2
    ################################################################################

    @api.model
    def _l10n_ro_edi_stock_validate_data(self, data: dict):
        errors = super()._l10n_ro_edi_stock_validate_data(data=data)

        op_type = data.get("l10n_ro_edi_stock_operation_type")
        if not op_type:
            return errors

        # BR-068/069/070/205: operation scope restricted by operation type
        allowed_scopes = OPERATION_TYPE_TO_ALLOWED_SCOPE_CODES_FULL.get(op_type)
        scope = data.get("l10n_ro_edi_stock_operation_scope")
        if allowed_scopes and scope and scope not in allowed_scopes:
            errors.append(
                self.env._(
                    "Operation scope %(scope)s is not allowed for type %(op)s. "
                    "Allowed values: %(allowed)s",
                    scope=scope,
                    op=op_type,
                    allowed=", ".join(allowed_scopes),
                )
            )

        # BR-005/004/006: partner country code vs operation
        partner = data["partner_id"].commercial_partner_id
        country_code = VALID_COUNTRY_CODE_MAP.get(
            partner.country_code, partner.country_code
        )
        if country_code:
            if is_national(op_type) and country_code != "RO":
                errors.append(
                    self.env._(
                        "For operation 30 (National transport), the "
                        "commercial partner must be from RO."
                    )
                )
            elif op_type in ("10", "12", "14", "20", "22", "24", "60", "70"):
                if country_code not in EU_COUNTRY_CODES or country_code == "RO":
                    errors.append(
                        self.env._(
                            "For operation %(op)s the partner country code "
                            "(%(cc)s) must be EU and different from RO.",
                            op=op_type,
                            cc=country_code,
                        )
                    )
            elif op_type in ("40", "50"):
                if country_code in EU_COUNTRY_CODES:
                    errors.append(
                        self.env._(
                            "For operation %(op)s (Import/Export) the partner "
                            "country code (%(cc)s) must be outside the EU.",
                            op=op_type,
                            cc=country_code,
                        )
                    )

        # BR-206/207/208: codTarifar / greutateNeta / valoareLeiFaraTva
        # are mandatory except for operations 60/70.
        if needs_goods_full_data(op_type):
            errors += self._l10n_ro_edi_stock_validate_goods_data(data)

        # BR-218/020/029: greutateBruta required, > 0, >= greutateNeta
        errors += self._l10n_ro_edi_stock_validate_weights(data)

        # Multi-doc validation (only if lines exist; otherwise fallback to base)
        picking = data.get("_picking_record")
        if picking and picking.l10n_ro_edi_stock_document_line_ids:
            errors += self._l10n_ro_edi_stock_validate_doc_lines(picking)

        # Previous notification mandatory for 60/70
        if op_type in ("60", "70"):
            if picking and not picking.l10n_ro_edi_stock_previous_ids:
                errors.append(
                    self.env._(
                        "For operation %(op)s at least one previous notification "
                        "is required.",
                        op=op_type,
                    )
                )

        return errors

    @api.model
    def _l10n_ro_edi_stock_validate_goods_data(self, data):
        errors = []
        picking = data.get("_picking_record")
        if not picking:
            return errors

        products_missing_tarifar = set()
        products_missing_value = set()
        products_missing_weight = set()

        for move in data["stock_move_ids"]:
            product = move.product_id
            tarifar = self._l10n_ro_edi_stock_get_codtarifar(product)
            if not tarifar:
                products_missing_tarifar.add(product.display_name)

            net_weight = picking._l10n_ro_edi_stock_compute_net_weight(move)
            if float_is_zero(net_weight, precision_digits=2):
                products_missing_weight.add(product.display_name)

            value = picking._l10n_ro_edi_stock_compute_value(
                move, data["l10n_ro_edi_stock_operation_type"]
            )
            if float_compare(value, 0.0, precision_digits=2) <= 0:
                products_missing_value.add(product.display_name)

        if products_missing_tarifar:
            errors.append(
                self.env._(
                    "The following products are missing a tariff (NC8) code: %(names)s",
                    names=", ".join(sorted(products_missing_tarifar)),
                )
            )
        if products_missing_weight:
            errors.append(
                self.env._(
                    "The following products have 0 net weight: %(names)s",
                    names=", ".join(sorted(products_missing_weight)),
                )
            )
        if products_missing_value:
            errors.append(
                self.env._(
                    "The following products have 0 value "
                    "(check the price source): %(names)s",
                    names=", ".join(sorted(products_missing_value)),
                )
            )
        return errors

    @api.model
    def _l10n_ro_edi_stock_validate_weights(self, data):
        errors = []
        picking = data.get("_picking_record")
        if not picking:
            return errors

        for move in data["stock_move_ids"]:
            net = picking._l10n_ro_edi_stock_compute_net_weight(move)
            gross = picking._l10n_ro_edi_stock_compute_gross_weight(move)
            if float_is_zero(gross, precision_digits=2):
                errors.append(
                    self.env._(
                        "Gross weight must be > 0 for %(p)s.",
                        p=move.product_id.display_name,
                    )
                )
            if float_compare(gross, net, precision_digits=2) < 0:
                errors.append(
                    self.env._(
                        "Gross weight (%(g)s) must be >= net weight (%(n)s) for %(p)s.",
                        g=gross,
                        n=net,
                        p=move.product_id.display_name,
                    )
                )
        return errors

    @api.model
    def _l10n_ro_edi_stock_validate_doc_lines(self, picking):
        errors = []
        for line in picking.l10n_ro_edi_stock_document_line_ids:
            if not line.document_type:
                errors.append(
                    self.env._("Document type is missing on an eTransport line.")
                )
            elif line.document_type == "9999" and not line.remarks:
                errors.append(
                    self.env._(
                        "When document type is 'Other' (9999) the remarks field "
                        "is mandatory (BR-026)."
                    )
                )
            if not line.document_date:
                errors.append(
                    self.env._("Document date is missing on an eTransport line.")
                )
        return errors

    ################################################################################
    # Allow sending the notification before the transfer is validated
    ################################################################################

    @api.depends("l10n_ro_edi_stock_enable", "state", "l10n_ro_edi_stock_state")
    def _compute_l10n_ro_edi_stock_enable_send(self):
        # EXTENDS l10n_ro_edi_stock
        # The base only allows sending once the picking is 'done'. ANAF must be
        # notified *before* the goods are moved, so allow it on any non-draft,
        # non-cancelled, not-yet-done transfer too (waiting/confirmed/assigned).
        res = super()._compute_l10n_ro_edi_stock_enable_send()
        for picking in self:
            if (
                not picking.l10n_ro_edi_stock_enable_send
                and picking.l10n_ro_edi_stock_enable
                and picking.state not in ("cancel", "done")
                and picking.l10n_ro_edi_stock_state in (False, "stock_sending_failed")
                and not picking._l10n_ro_edi_stock_get_last_document("stock_validated")
            ):
                picking.l10n_ro_edi_stock_enable_send = True
        return res

    ################################################################################
    # Override template data computation
    ################################################################################

    def _l10n_ro_edi_stock_send_etransport_document(self, send_type: str):
        # Override: pass self via context so the override of
        # _l10n_ro_edi_stock_get_template_data can access the picking record
        # (price source, doc lines, previous notifications, post-outage flag).
        self.ensure_one()
        return super(
            StockPicking,
            self.with_context(
                l10n_ro_edi_stock_extension_picking=self.id,
            ),
        )._l10n_ro_edi_stock_send_etransport_document(send_type=send_type)

    @api.model
    def _l10n_ro_edi_stock_get_template_data(self, data: dict):
        picking_id = self.env.context.get("l10n_ro_edi_stock_extension_picking")
        if picking_id:
            data["_picking_record"] = self.browse(picking_id)
        result = super()._l10n_ro_edi_stock_get_template_data(data=data)
        picking = data.get("_picking_record")
        if not picking:
            return result

        template = result["data"]
        op_type = data["l10n_ro_edi_stock_operation_type"]

        # ------- bunuriTransportate: rebuild with correct sources -------
        goods = []
        for move in data["stock_move_ids"]:
            product = move.product_id
            qty_in_decl_uom, decl_uom_code = picking._l10n_ro_edi_stock_get_qty_and_uom(
                move
            )
            net = picking._l10n_ro_edi_stock_compute_net_weight(move)
            gross = picking._l10n_ro_edi_stock_compute_gross_weight(move)
            if float_compare(gross, net, precision_digits=2) < 0:
                gross = net  # safety net for BR-020

            unit_value = picking._l10n_ro_edi_stock_compute_value(move, op_type)
            line_total_value = unit_value * qty_in_decl_uom
            entry = {
                "codScopOperatiune": data["l10n_ro_edi_stock_operation_scope"],
                "codTarifar": picking._l10n_ro_edi_stock_get_codtarifar(product),
                "denumireMarfa": (product.name or "")[:200],
                "cantitate": float_round(qty_in_decl_uom, precision_digits=2),
                "codUnitateMasura": decl_uom_code,
                "greutateNeta": float_round(net, precision_digits=2),
                "greutateBruta": float_round(gross, precision_digits=2),
                "valoareLeiFaraTva": float_round(line_total_value, precision_digits=2),
            }
            if not needs_goods_full_data(op_type):
                # For op. 60/70 codTarifar/greutateNeta/valoareLeiFaraTva are optional
                entry["codTarifar"] = entry["codTarifar"] or None
                if float_is_zero(entry["greutateNeta"], precision_digits=2):
                    entry["greutateNeta"] = None
                if float_is_zero(entry["valoareLeiFaraTva"], precision_digits=2):
                    entry["valoareLeiFaraTva"] = None
            goods.append(entry)
        template["notificare"]["bunuriTransportate"] = goods

        # ------- locations: street/number split -------
        for loc_key, loc_kind in (
            ("locStartTraseuRutier", "start"),
            ("locFinalTraseuRutier", "end"),
        ):
            loc_entry = template["notificare"].get(loc_key) or {}
            if loc_entry.get("location_type") != "location":
                continue
            partner = picking._l10n_ro_edi_stock_resolve_address_partner(
                loc_kind, op_type
            )
            if not partner:
                continue
            street_parts = picking._l10n_ro_edi_stock_split_street(partner.street or "")
            locatie = loc_entry.get("locatie") or {}
            locatie["denumireStrada"] = street_parts["denumireStrada"]
            if street_parts["numar"]:
                locatie["numar"] = street_parts["numar"]
            if partner.street2:
                locatie["alteInfo"] = partner.street2
            loc_entry["locatie"] = locatie

        # ------- declPostAvarie -------
        if picking.l10n_ro_edi_stock_post_outage:
            template["declPostAvarie"] = "D"

        # ------- multiple transport documents -------
        if picking.l10n_ro_edi_stock_document_line_ids:
            template["notificare"]["documenteTransport"] = [
                {
                    "tipDocument": line.document_type,
                    "numarDocument": line.document_number or picking.name,
                    "dataDocument": line.document_date,
                    "observatii": line.remarks,
                }
                for line in picking.l10n_ro_edi_stock_document_line_ids
            ]
        else:
            # Keep the old single-dict template format; convert to a list to
            # simplify the Qweb template.
            single_doc = template["notificare"]["documenteTransport"]
            if isinstance(single_doc, dict):
                template["notificare"]["documenteTransport"] = [single_doc]

        # ------- notificareAnterioara -------
        if picking.l10n_ro_edi_stock_previous_ids:
            template["notificare"]["notificariAnterioare"] = [
                {
                    "uit": prev.uit,
                    "observatii": prev.remarks,
                    "refDeclarant": prev.declarant_ref,
                }
                for prev in picking.l10n_ro_edi_stock_previous_ids
            ]

        # ------- refDeclarant truncated to 50 chars (Str50 XSD) -------
        if template.get("refDeclarant"):
            template["refDeclarant"] = template["refDeclarant"][:50]

        return {"data": template}

    ################################################################################
    # New helpers - price source, quantity, weights, address, codTarifar
    ################################################################################

    def _l10n_ro_edi_stock_compute_value(self, move, op_type):
        """Return the valoareLeiFaraTva according to the configured price source.

        - auto: incoming -> cost (or PO line if the transfer is not validated),
                outgoing -> SO line price_unit (or list_price fallback).
        - explicit: cost / purchase / sale / list.
        Values are converted into RON (company currency) when the original
        is in a different currency.
        """
        self.ensure_one()
        company_currency = self.company_id.currency_id
        source = self.l10n_ro_edi_stock_price_source or "auto"
        if source == "auto":
            if is_outgoing(op_type) or (
                is_national(op_type) and self.picking_type_code == "outgoing"
            ):
                source = "sale"
            else:
                source = "cost"
        value = 0.0
        if source == "cost":
            value = self._l10n_ro_edi_stock_value_from_cost(move)
            if float_is_zero(value, precision_digits=2):
                value = self._l10n_ro_edi_stock_value_from_purchase(move)
        elif source == "purchase":
            value = self._l10n_ro_edi_stock_value_from_purchase(move)
            if float_is_zero(value, precision_digits=2):
                value = self._l10n_ro_edi_stock_value_from_cost(move)
        elif source == "sale":
            value = self._l10n_ro_edi_stock_value_from_sale(move)
            if float_is_zero(value, precision_digits=2):
                value = move.product_id.list_price
        elif source == "list":
            value = move.product_id.list_price

        # Convert to RON (company currency)
        product_currency = move.product_id.currency_id or company_currency
        if value and product_currency != company_currency:
            value = product_currency._convert(
                value,
                company_currency,
                self.company_id,
                self.scheduled_date or fields.Date.context_today(self),
            )
        return value

    def _l10n_ro_edi_stock_value_from_cost(self, move):
        """Average / standard cost from the product, or - when the transfer is
        validated - the accounting value of the move (stock.move.price_unit is
        in company currency after validation).
        """
        if self.state == "done" and move.price_unit:
            return abs(move.price_unit)
        return move.product_id.standard_price

    def _l10n_ro_edi_stock_value_from_purchase(self, move):
        po_line = move.purchase_line_id
        if po_line:
            currency = po_line.currency_id or po_line.order_id.currency_id
            company_currency = self.company_id.currency_id
            price = po_line.price_unit
            if currency and currency != company_currency:
                price = currency._convert(
                    price,
                    company_currency,
                    self.company_id,
                    po_line.order_id.date_order
                    or self.scheduled_date
                    or fields.Date.context_today(self),
                )
            return price
        return 0.0

    def _l10n_ro_edi_stock_value_from_sale(self, move):
        so_line = move.sale_line_id
        if so_line:
            currency = so_line.currency_id or so_line.order_id.currency_id
            company_currency = self.company_id.currency_id
            # SO price_unit is always net of taxes in Odoo
            price = so_line.price_unit
            if currency and currency != company_currency:
                price = currency._convert(
                    price,
                    company_currency,
                    self.company_id,
                    so_line.order_id.date_order
                    or self.scheduled_date
                    or fields.Date.context_today(self),
                )
            return price
        return 0.0

    def _l10n_ro_edi_stock_get_qty_and_uom(self, move):
        """Return a consistent (quantity, codUnitateMasura) pair.

        The official module emitted ``move.product_qty`` (quantity converted
        to the product base UoM) with the UNECE code of ``move.product_uom``,
        which was inconsistent. Here we emit both the quantity and the UNECE
        code in the same UoM (``move.product_uom``).
        """
        uom = move.product_uom or move.product_id.uom_id
        if move.state == "done" and "quantity" in move._fields:
            qty = move.quantity
        else:
            qty = move.product_uom_qty
        code = uom._get_unece_code() if uom else "H87"
        # ANAF accepts 2-3 character codes [A-Z0-9]
        if code and len(code) > 3:
            code = code[:3]
        return qty, code or "H87"

    def _l10n_ro_edi_stock_compute_net_weight(self, move):
        """Net weight = product weight * quantity in the product base UoM."""
        product = move.product_id
        qty_base = move.product_uom._compute_quantity(
            move.quantity if move.state == "done" else move.product_uom_qty,
            product.uom_id,
        )
        return (product.weight or 0.0) * qty_base

    def _l10n_ro_edi_stock_compute_gross_weight(self, move):
        """Gross weight = net weight + packaging weight.

        Packaging weight: for each unique package touched by move.move_lines
        add only once (shipping_weight - weight), or if shipping_weight is
        missing, fall back to package_type_id.base_weight (empty packaging).
        """
        net = self._l10n_ro_edi_stock_compute_net_weight(move)
        packaging_extra = 0.0
        seen_packages = set()
        for line in move.move_line_ids:
            pkg = line.result_package_id
            if not pkg or pkg.id in seen_packages:
                continue
            seen_packages.add(pkg.id)
            ship_w = pkg.shipping_weight or pkg.weight or 0.0
            # Difference between shipping_weight (loaded) and weight (empty)
            # is the packaging weight
            empty_w = pkg.package_type_id.base_weight if pkg.package_type_id else 0.0
            packaging_extra += max(empty_w, ship_w - (pkg.weight or 0.0))
        return net + packaging_extra

    def _l10n_ro_edi_stock_get_codtarifar(self, product):
        """Valid codTarifar (NC8/HS code): 4, 6 or 8 digits.

        Looks at product.product, then product.template, then the category.
        Returns None when no valid code is found (no 00000000 fallback).
        """
        if "intrastat_code_id" in product._fields and product.intrastat_code_id.code:
            code = re.sub(r"\D", "", product.intrastat_code_id.code)
            if re.fullmatch(r"\d{4}|\d{6}|\d{8}", code):
                return code
        # Fallback to product category if the field exists there
        if (
            "intrastat_code_id" in product.categ_id._fields
            and product.categ_id.intrastat_code_id.code
        ):
            code = re.sub(r"\D", "", product.categ_id.intrastat_code_id.code)
            if re.fullmatch(r"\d{4}|\d{6}|\d{8}", code):
                return code
        return None

    def _l10n_ro_edi_stock_resolve_address_partner(self, loc_kind, op_type):
        self.ensure_one()
        code = self.picking_type_id.code
        warehouse_partner = self.picking_type_id.warehouse_id.partner_id
        if code == "outgoing":
            return warehouse_partner if loc_kind == "start" else self.partner_id
        if code == "incoming":
            return warehouse_partner if loc_kind == "end" else self.partner_id
        # internal or other types - use warehouse for start, partner for end
        return warehouse_partner if loc_kind == "start" else self.partner_id

    @api.model
    def _l10n_ro_edi_stock_split_street(self, street):
        """Split "Calea Victoriei 12-14" -> denumireStrada="Calea Victoriei",
        numar="12-14". On parse failure, return the whole string as denumireStrada.
        """
        if not street:
            return {"denumireStrada": "", "numar": None}
        match = _STREET_NUMBER_PATTERN.match(street.strip())
        if not match:
            return {"denumireStrada": street.strip()[:100], "numar": None}
        nume = (match.group(1) or "").strip()
        nr = (match.group(2) or "").strip() or None
        rest = (match.group(3) or "").strip()
        denumire = (nume + (" " + rest if rest else "")).strip()
        return {
            "denumireStrada": (denumire or street.strip())[:100],
            "numar": nr[:20] if nr else None,
        }
