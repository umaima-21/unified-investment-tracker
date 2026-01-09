"""
Script to add folio_number support to mutual_fund_service.py
"""

file_path = r'backend\services\mutual_fund_service.py'

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.splitlines(keepends=True)

print(f"Total lines: {len(lines)}")

# Line 133 (index 132) should have "units = float(holding_data"
target_line = 132  # 0-indexed

if target_line >= len(lines):
    print(f"File only has {len(lines)} lines!")
    exit(1)

print(f"Line {target_line + 1}: {lines[target_line].strip()}")

# Verify this is the right location
if "units = float(holding_data" not in lines[target_line]:
    print("Wrong line! Searching...")
    for i, line in enumerate(lines):
        if "units = float(holding_data.get('units'" in line:
            print(f"Found at line {i+1}: {line.strip()}")

# Insert folio extraction after line 136 (index 135)
# Line 136 should be "if current_value:"
# Line 137 should be "current_value = float(current_value)"
# We insert after line 137

insertion_point = 137  # After "current_value = float(current_value)"

print(f"\nInserting folio extraction after line {insertion_point + 1}")

# Insert the lines
lines.insert(insertion_point, "            \n")
lines.insert(insertion_point + 1, "            # Extract folio number from CAS data\n")
lines.insert(insertion_point + 2, "            folio_number = holding_data.get('folio')\n")

# Now modify line with "current_value=current_value" in Holding() to add comma
# This should be around line 143 (now shifted by 3 lines = 146)
for i in range(140, 150):
    if i < len(lines) and "current_value=current_value" in lines[i]:
        print(f"\nFound Holding() current_value line at {i+1}: {lines[i].strip()}")
        # Add comma if not already there
        if lines[i].rstrip().endswith("current_value"):
            lines[i] = lines[i].rstrip() + ",\n"
            # Insert folio_number line
            lines.insert(i + 1, "                    folio_number=folio_number  # Store folio number\n")
            print(f"Added folio_number parameter after line {i+1}")
        break

# Find else block and add folio update
# Look for "holding.current_value = current_value" in the else block
for i in range(145, 160):
    if i < len(lines) and "holding.current_value = current_value" in lines[i]:
        # Check if this is in the else block
        found_else = False
        for j in range(max(0, i-5), i):
            if "else:" in lines[j]:
                found_else = True
                break
        
        if found_else:
            print(f"\nFound else block update at line {i+1}: {lines[i].strip()}")
            # Insert after this line
            lines.insert(i + 1, "                # Update folio number if available\n")
            lines.insert(i + 2, "                if folio_number:\n")
            lines.insert(i + 3, "                    holding.folio_number = folio_number\n")
            print(f"Added folio update logic after line {i+1}")
            break

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\n✅ Successfully updated mutual_fund_service.py with folio_number support!")
