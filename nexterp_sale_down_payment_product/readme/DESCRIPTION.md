In Odoo 19 the down payment lines created on a sale order (and the
related down payment invoice lines) have no product. This module adds
a company-level **Down Payment Product** setting; when it is set, the
product is added on every new down payment sale order line and on the
down payment invoice line.

The income account of the down payment invoice line is also taken from
this product when no company *Down Payment Account* is configured.
