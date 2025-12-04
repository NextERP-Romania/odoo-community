# mrp_subcontracting_price

This Odoo module extends subcontracting functionality in Manufacturing (MRP) to support
price management for subcontracted operations.

## Features

- Adds price fields and logic to stock moves related to subcontracting
- Integrates with Odoo's MRP and stock modules
- Designed for Odoo 19.0 community edition

## Directory Structure

- `models/stock_move.py`: Main logic for price handling on subcontracted stock moves
- `models/__init__.py`: Model imports
- `__manifest__.py`: Module manifest
- `__init__.py`: Module init
- `readme/`: Documentation directory

## Installation

1. Copy the module to your Odoo addons directory.
2. Update the app list and install `mrp_subcontracting_price` from the Odoo interface.

## Usage

- When processing subcontracting operations, price fields will be available and managed
  automatically.
- See `models/stock_move.py` for extension logic.

## Author

NextERP Romania
