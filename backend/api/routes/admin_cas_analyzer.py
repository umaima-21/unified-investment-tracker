"""
Analyze CAS file endpoint
"""
from fastapi import APIRouter, Query
from pathlib import Path
import PyPDF2
import pdfplumber
from loguru import logger
from connectors.cas_parser import CASParser

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/analyze-cas")
async def analyze_cas(
    filename: str = Query(None, description="CAS filename to analyze (optional, uses latest if not provided)"),
    password: str = Query("", description="PDF password (optional)")
):
    """Analyze the uploaded CAS file"""
    
    upload_dir = Path("uploads/cas")
    
    # Find the file to analyze
    if filename:
        # Try exact match first
        pdf_path = upload_dir / filename
        if not pdf_path.exists():
            # Try case-insensitive search
            pdf_files = [f for f in upload_dir.glob("*") if f.name.lower() == filename.lower()]
            if pdf_files:
                pdf_path = pdf_files[0]
            else:
                # Try partial match (in case extension is different)
                pdf_files = [f for f in upload_dir.glob(f"*{filename.split('.')[0]}*")]
                if pdf_files:
                    pdf_path = pdf_files[0]
    else:
        # Get the most recently uploaded file
        pdf_files = list(upload_dir.glob("*.pdf*"))
        if not pdf_files:
            return {"error": "No CAS files found in uploads/cas"}
        pdf_path = max(pdf_files, key=lambda p: p.stat().st_mtime)
    
    if not pdf_path.exists():
        return {"error": f"File not found: {pdf_path}"}
    
    results = {
        "file": str(pdf_path),
        "filename": pdf_path.name,
        "text_samples": [],
        "tables_found": 0,
        "parsing_results": {}
    }
    
    # Try with pdfplumber
    try:
        with pdfplumber.open(pdf_path, password=password if password else None) as pdf:
            results["total_pages"] = len(pdf.pages)
            
            # Get text from first 3 pages
            for i, page in enumerate(pdf.pages[:3]):
                text = page.extract_text()
                if text:
                    results["text_samples"].append({
                        "page": i + 1,
                        "text": text[:2000],  # First 2000 chars
                        "full_length": len(text)
                    })
                
                # Try to extract tables
                tables = page.extract_tables()
                if tables:
                    results["tables_found"] += len(tables)
                    if i == 0:  # Show tables from first page
                        results["first_page_tables"] = [
                            {
                                "rows": len(table),
                                "columns": len(table[0]) if table else 0,
                                "sample": table[:3] if len(table) > 3 else table  # First 3 rows
                            }
                            for table in tables[:2]  # First 2 tables
                        ]
                    
    except Exception as e:
        results["error"] = str(e)
        logger.error(f"Error analyzing CAS: {e}")
        import traceback
        results["traceback"] = traceback.format_exc()
    
    # Try parsing with CAS parser
    try:
        parser = CASParser(str(pdf_path), password if password else None)
        parsed_data = parser.parse()
        
        results["parsing_results"] = {
            "text_extracted": len(parser.text_content),
            "holdings_found": len(parsed_data.get("holdings", [])),
            "transactions_found": len(parsed_data.get("transactions", [])),
            "investor_info": parsed_data.get("investor_info", {}),
            "sample_holdings": parsed_data.get("holdings", [])[:3],  # First 3 holdings
            "sample_transactions": parsed_data.get("transactions", [])[:3],  # First 3 transactions
            "text_preview": parser.text_content[:1000] if parser.text_content else "No text extracted"
        }
    except Exception as e:
        results["parsing_error"] = str(e)
        logger.error(f"Error parsing CAS: {e}")
        import traceback
        results["parsing_traceback"] = traceback.format_exc()
    
    return results
