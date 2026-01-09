"""
Patch for mutual_fund_service.py to add folio_number support

Apply this patch by copying the code below into the _import_holding method
"""

# Replace lines 133-151 with:

units = float(holding_data.get('units', 0) or 0)
current_value = holding_data.get('current_value')
if current_value:
    current_value = float(current_value)

# Extract folio number from CAS data
folio_number = holding_data.get('folio')

if not holding:
    holding = Holding(
        asset_id=asset.asset_id,
        quantity=units,
        invested_amount=0,  # Will calculate from transactions
        current_value=current_value,
        folio_number=folio_number  # Store folio number
    )
    self.db.add(holding)
else:
    # Update existing holding - aggregate quantities if needed
    holding.quantity = units
    if current_value:
        holding.current_value = current_value
    # Update folio number if available
    if folio_number:
        holding.folio_number = folio_number
