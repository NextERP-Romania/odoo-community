# Key features

- **Automatic CIUS-RO field truncation** — party names, addresses, document references, payment means, allowance/charge reasons, VAT exemption reasons, and line item names/descriptions are silently truncated to their ANAF-mandated limits.
- **Smart note splitting** — invoice notes (BT-22) and line notes (BT-127) are split into multiple `cbc:Note` tags of ≤ 300 characters and ≤ 300 UTF-8 bytes instead of being truncated.
- **Prevents ANAF SPV rejection** — enforces schematron rules BR-RO-L020 through BR-RO-L1000 so e-Factura XML passes ANAF validation without manual intervention.
- **Zero-configuration** — installed automatically alongside `l10n_ro_edi_extension` (`auto_install`); no setup required.
- **Unicode-aware length counting** — character lengths are counted as Unicode code points, matching the XPath `string-length` function used by the ANAF validator.
