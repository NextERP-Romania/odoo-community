# BOM Excel Import Module

This Odoo 19.0 module allows importing Bills of Materials (BOMs) from Excel files using
a unified wizard with a two-step process:

1. **Import Operations and Workcenters** (automatically performed first)
2. **Import BOMs with routing operations** (performed second)

## Excel File Structure

The Excel file should have the following columns:

| Column | Description        | Required | Example                        |
| ------ | ------------------ | -------- | ------------------------------ |
| A      | Product produced   | Yes      | "Finished Product A"           |
| B      | Operation name     | No       | "Cutting", "Assembly"          |
| C      | Quantity consumed  | Yes      | 2.5, 1.0                       |
| D      | Component UOM      | Yes      | "Unit"                         |
| E      | Component consumed | Yes      | "Raw Material B"               |
| F      | Workcenter name    | No       | "CNC Machine", "Assembly Line" |

## Example Excel Data

```
Product Produced    | Operation  | Quantity | Component UOM | Component      | Workcenter
-------------------|------------|----------|----------------|------------------
Chair              | Cutting    | 4        | Unit           | Wood Plank     | Saw Machine
Chair              | Assembly   | 8        | Unit           | Screw          | Assembly Line
Chair              | Assembly   | 1        | Unit           | Cushion        | Assembly Line
Table              | Cutting    | 1        | Unit           | Wood Board     | Saw Machine
Table              | Assembly   | 4        | Unit           | Table Leg      | Assembly Line
Table              | Assembly   | 12       | Unit           | Screw          | Assembly Line
```

## Import Process

### Using the Unified Wizard

1. Go to **Manufacturing > Configuration > BOM Excel Import**
2. Upload your Excel file and configure settings
3. Click "Start Import" to begin the process
4. The wizard will guide you through:
   - **Step 1**: File validation and configuration
   - **Step 2**: Import operations and workcenters
   - **Step 3**: Import BOMs with components and routing
   - **Step 4**: View import summary and results

### Step-by-Step Process

1. **Upload File**: Select your Excel file, specify sheet name and start row
2. **Import Operations**: Creates workcenters and routing operations from the Excel data
3. **Import BOMs**: Creates products, BOMs, and BOM lines with proper operation linking
4. **Complete**: Review the import summary and detailed logs

## Features

- **Unified Two-Step Process**: Single wizard handles the complete import workflow
- **Automatic Product Creation**: Products are created automatically if they don't exist
- **Duplicate Detection**: Skips existing BOMs and workcenters
- **Error Handling**: Detailed import logs with error reporting for each step
- **Operation Linking**: Links BOM components to specific operations
- **Flexible Format**: Handles missing optional columns gracefully
- **Progress Tracking**: Clear indication of current step and progress
- **Detailed Logging**: Separate logs for operations and BOM import steps

## Requirements

- Odoo 19.0
- Python library: `openpyxl` (for Excel file processing)

## Installation

1. Copy the module to your Odoo addons directory
2. Install the `openpyxl` Python library:
   ```bash
   pip install openpyxl
   ```
3. Update the module list in Odoo
4. Install the "BOM Excel Import" module

## Troubleshooting

### Common Issues

1. **"openpyxl library is required"**
   - Install openpyxl: `pip install openpyxl`

2. **"Could not find product"**
   - Products are created automatically, but check the product names in your Excel file

3. **"BOM already exists"**
   - The module skips existing BOMs. Delete existing BOMs if you want to reimport

4. **"Workcenter not found"**
   - This shouldn't happen as workcenters are created in the first step

### Import Logs

The wizard provides detailed import logs for both steps showing:

- Number of records processed in each step
- Created workcenters, operations, BOMs, and BOM lines
- Error messages with row numbers
- Warnings and informational messages
- Import summary with totals

## Technical Details

### Models Created

- `bom.excel.import.wizard`: Unified wizard handling both import steps

### Dependencies

- `mrp`: Manufacturing module
- `stock`: Inventory module
- `base`: Base Odoo functionality

### Menu Location

Manufacturing > Configuration > BOM Excel Import

## Support

This module was created for NextERP Romania. For support, please contact the development
team.
