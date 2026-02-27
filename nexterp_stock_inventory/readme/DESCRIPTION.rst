Stock Inventory Management for Romanian Localization
=====================================================

This module provides an enhanced stock inventory management system specifically designed for Romanian localization requirements, offering comprehensive tools for physical inventory adjustments with proper accounting traceability.

Key Features
------------
**Inventory Document Management**
  - Create and manage stock inventory documents with accounting dates
  - Track inventory states (Draft/Done) with proper validation workflow
  - Filter by specific locations and products for targeted inventory counts

**Automated Line Generation**
  - Automatically generate inventory lines based on current stock quantities
  - Smart detection to avoid duplicate lines for existing quants
  - Support for multiple locations and products selection
  - Preserve original on-hand quantities for accurate difference tracking

**Comprehensive Value Tracking**
  - Track both quantity and monetary value differences
  - Calculate inventory adjustments with proper accounting dates
  - Maintain historical records of inventory before and after validation
  - Support for standard cost valuation

**Advanced Quant Integration**
  - Seamless integration with Odoo's stock quant system
  - Automatic inventory document creation when quants are adjusted outside the standard workflow
  - Bi-directional synchronization between inventory lines and stock quantities
  - Context-aware processing to prevent recursive inventory creation


Workflow
--------
1. **Create Inventory**: Create a new inventory document with accounting date
2. **Select Scope**: Choose specific locations and/or products (optional)
3. **Generate Inventory Lines**: Automatically populate inventory lines from current stock. 
4. **Or Create Inventory Lines & Stock Quants**: Create stock quant directly from inventory line if it doesn't exist for the given location/product/lot.
5. **Count & Adjust**: Enter counted quantities for each inventory line
6. **Validate**: Apply adjustments to stock and finalize the inventory


Technical Details
-----------------
- **Models**: `l10n.ro.stock.inventory` and `l10n.ro.stock.inventory.line`
- **Dependencies**: `stock_account`
- **Integration**: Extends `stock.quant` for automatic inventory creation
- **Security**: Proper access controls with configurable user permissions
- **Data Integrity**: SQL constraints to prevent duplicate quant entries
