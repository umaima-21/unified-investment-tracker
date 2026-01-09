#!/usr/bin/env python
"""Test script for CAS parser"""
import sys
sys.path.insert(0, '.')
from connectors.cas_parser_llm import CASParserLLM

pdf_path = 'uploads/cas/NSDLe-CAS_102969940_NOV_2025.PDF'
password = 'ADPPT7723B'

print("Testing CAS Parser...")
parser = CASParserLLM(pdf_path, password)
result = parser.parse()

print(f"\nTotal holdings found: {len(result.get('holdings', []))}")
print("\nHoldings:")
for i, h in enumerate(result.get('holdings', []), 1):
    print(f"  {i}. {h.get('scheme_name', 'N/A')}")
    print(f"     Units: {h.get('units', 0)}, Invested: {h.get('invested_amount', 0)}, Value: {h.get('current_value', 0)}")
    print(f"     Plan: {h.get('plan_type', 'N/A')}, Option: {h.get('option_type', 'N/A')}")

