"""
Analyze CAS PDF file to understand its format
"""
import sys
sys.path.append('backend')

import PyPDF2
import pdfplumber
from pathlib import Path

pdf_path = 'uploads/cas/ADXXXXXX3B_01012003-24112025_CP198977066_24112025032830287.pdf'
password = '1234567890'

print(f"Analyzing CAS file: {pdf_path}\n")
print("=" * 80)

# Try with pdfplumber first
try:
    print("\n### Using pdfplumber ###\n")
    with pdfplumber.open(pdf_path, password=password) as pdf:
        print(f"Total pages: {len(pdf.pages)}\n")
        
        # Extract text from first 2 pages
        for i, page in enumerate(pdf.pages[:2]):
            print(f"\n--- PAGE {i+1} ---")
            text = page.extract_text()
            if text:
                # Print first 2000 characters
                print(text[:2000])
                print("\n[... truncated ...]")
            else:
                print("(No text extracted)")
                
except Exception as e:
    print(f"pdfplumber error: {e}")

# Try with PyPDF2
try:
    print("\n\n### Using PyPDF2 ###\n")
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        if pdf_reader.is_encrypted:
            pdf_reader.decrypt(password)
            print(f"PDF decrypted successfully")
        
        print(f"Total pages: {len(pdf_reader.pages)}\n")
        
        # Extract text from first page
        text = pdf_reader.pages[0].extract_text()
        if text:
            print(f"--- PAGE 1 ---")
            print(text[:2000])
            print("\n[... truncated ...]")
        else:
            print("(No text extracted)")
            
except Exception as e:
    print(f"PyPDF2 error: {e}")

print("\n" + "=" * 80)
print("Analysis complete!")
