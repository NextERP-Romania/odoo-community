# Usage

## Reviewing exceptions on a Purchase Order line

Exceptions defined in `purchase_exception` are normally visible at the Purchase Order header level. With this module installed, each individual order line also surfaces its own exception status.

1. Open a Purchase Order via **Purchase → Orders → Purchase Orders**.
2. Select or create a purchase order and navigate to the **Order Lines** tab.
3. Lines that violate one or more exception rules show a danger indicator (`is_exception_danger`) and a colour-coded **Exceptions** summary (`exceptions_summary`) directly on the line — no need to open a separate dialog to identify which line is causing the issue.
4. Hover over or click the exceptions indicator on the line to read the full `exception_ids` list of triggered `exception.rule` records.
5. Resolve the underlying data issue (e.g. adjust quantity, price or product) and re-validate the order. The exception indicators clear automatically once the rules no longer fire.
