Fuel, parts and services for company vehicles are bought on vendor bills
and taken out of the warehouse, but the fleet only knows about the costs
typed in by hand. This module books the vehicle costs straight from the
bills and from the stock issued to the vehicles.

- **Vehicle Service Type** on vendor bill lines: posting the bill records
  the cost on the vehicle, with product, quantity and unit price.
- **Vehicle** on stock moves: goods issued to a consumption location for a
  vehicle become a vehicle cost when the transfer is validated.
- Goods returned from the vehicle book a negative cost that reverses the
  original one; cancelling a bill removes the costs it created.
- Costs booked from stock follow their move and cannot be edited or
  deleted by hand.
- **Owner** on the vehicle, carried to every service and contract cost.
- Romanian non-deductible VAT per vehicle: a percentage and a tax applied
  to the goods it consumes.
- **Costs Log** report, in pivot and list, per vehicle, type and date.
- Fuel and parts service type categories, with a ready-made refuelling
  service type.
