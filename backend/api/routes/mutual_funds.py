"""
Mutual Funds API Routes.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
import shutil
import traceback
import uuid
from loguru import logger

from database import get_db
from services.mutual_fund_service import MutualFundService
from models.holdings import Holding


router = APIRouter()


# Pydantic models for request/response
class SchemeSearchResponse(BaseModel):
    schemeCode: str
    schemeName: str


class AddSchemeRequest(BaseModel):
    scheme_code: str
    units: float
    invested_amount: float


class HoldingResponse(BaseModel):
    holding_id: str
    asset_id: str
    quantity: float
    invested_amount: float
    current_value: Optional[float]
    unrealized_gain: Optional[float]
    unrealized_gain_percentage: Optional[float]
    

@router.get("/parser-status")
async def get_parser_status():
    """
    Check which CAS parser is available and configured.
    Returns status of OpenAI API configuration.
    """
    try:
        from config.settings import settings
        from connectors.cas_parser_llm import OPENAI_AVAILABLE
        
        openai_key_set = bool(settings.OPENAI_API_KEY)
        openai_key_preview = settings.OPENAI_API_KEY[:8] + "..." if settings.OPENAI_API_KEY else None
        configured_model = settings.OPENAI_MODEL if openai_key_set else None
        validated_model = settings.openai_model_validated if openai_key_set else None
        model_is_valid = configured_model == validated_model if configured_model else True
        
        status = {
            "openai_library_installed": OPENAI_AVAILABLE,
            "openai_api_key_configured": openai_key_set,
            "openai_api_key_preview": openai_key_preview,
            "openai_model_configured": configured_model,
            "openai_model_to_use": validated_model,
            "model_is_valid": model_is_valid,
            "parser_to_use": "LLM (OpenAI)" if (OPENAI_AVAILABLE and openai_key_set) else "Regex (fallback)",
            "recommendation": None
        }
        
        if not OPENAI_AVAILABLE:
            status["recommendation"] = "Install OpenAI: pip install openai"
        elif not openai_key_set:
            status["recommendation"] = "Add OPENAI_API_KEY=sk-your-key to .env file and restart the server"
        elif not model_is_valid:
            status["recommendation"] = f"WARNING: Invalid model '{configured_model}' in .env. Using '{validated_model}' instead. Valid models: gpt-4o, gpt-4o-mini, gpt-4, gpt-4-turbo, gpt-3.5-turbo"
        else:
            status["recommendation"] = "LLM parser is ready! Clear existing data and re-import your CAS file."
        
        return status
    except Exception as e:
        logger.error(f"Failed to get parser status: {e}")
        return {"error": str(e)}


@router.get("/holdings", response_model=List[dict])
async def get_mutual_fund_holdings(db: Session = Depends(get_db)):
    """
    Get all mutual fund holdings.
    
    Returns list of holdings with latest NAV and valuations.
    """
    try:
        service = MutualFundService(db)
        holdings = service.get_all_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Failed to get holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-cas")
async def import_cas_file(
    file: UploadFile = File(...),
    password: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload and import CAS PDF file.
    
    - **file**: CAS PDF file
    - **password**: PDF password (usually email + DOB)
    """
    try:
        # Validate file type (allow .pdf and .pdfy extensions)
        filename_lower = file.filename.lower()
        if not (filename_lower.endswith('.pdf') or filename_lower.endswith('.pdfy')):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Create upload directory if not exists
        upload_dir = Path("uploads/cas")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded CAS file: {file_path}, Password provided: {'Yes' if password else 'No'}")
        if password:
            logger.info(f"Password length: {len(password)} characters")
        
        # Parse and import CAS
        service = MutualFundService(db)
        result = service.import_from_cas(str(file_path), password)
        
        return result
        
    except Exception as e:
        logger.error(f"CAS import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()


@router.post("/update-nav")
async def update_nav_prices(
    scheme_codes: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Update NAV prices for mutual funds.
    
    - **scheme_codes**: Optional list of scheme codes to update. If not provided, updates all.
    """
    try:
        service = MutualFundService(db)
        result = service.update_nav_prices(scheme_codes)
        return result
    except Exception as e:
        logger.error(f"NAV update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_schemes(
    q: str,
    db: Session = Depends(get_db)
):
    """
    Search for mutual fund schemes by name.
    
    - **q**: Search query
    """
    try:
        if len(q) < 3:
            raise HTTPException(status_code=400, detail="Search query must be at least 3 characters")
        
        service = MutualFundService(db)
        results = service.search_schemes(q)
        return {"results": results}
    except Exception as e:
        logger.error(f"Scheme search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add-scheme")
async def add_scheme_manually(
    request: AddSchemeRequest,
    db: Session = Depends(get_db)
):
    """
    Manually add a mutual fund scheme with holdings.
    
    - **scheme_code**: MFAPI scheme code
    - **units**: Number of units held
    - **invested_amount**: Total invested amount
    """
    try:
        if request.units <= 0:
            raise HTTPException(status_code=400, detail="Units must be greater than 0")
        
        if request.invested_amount <= 0:
            raise HTTPException(status_code=400, detail="Invested amount must be greater than 0")
        
        service = MutualFundService(db)
        result = service.add_scheme_manually(
            scheme_code=request.scheme_code,
            units=request.units,
            invested_amount=request.invested_amount
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to add scheme'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add scheme: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheme/{scheme_code}")
async def get_scheme_details(
    scheme_code: str,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific scheme from MFAPI.
    
    - **scheme_code**: MFAPI scheme code
    """
    try:
        service = MutualFundService(db)
        nav_data = service.mfapi.get_latest_nav(scheme_code)
        
        if not nav_data:
            raise HTTPException(status_code=404, detail="Scheme not found")
        
        return nav_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch scheme details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a mutual fund transaction.
    
    - **transaction_id**: UUID of the transaction to delete
    """
    try:
        service = MutualFundService(db)
        result = service.delete_transaction(transaction_id)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to delete transaction'))
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/holdings/{asset_id}")
async def delete_holding(
    asset_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a single mutual fund holding and its associated data.
    
    - **asset_id**: UUID of the asset to delete
    """
    try:
        service = MutualFundService(db)
        result = service.delete_holding(asset_id)
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to delete holding'))
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete holding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/holdings")
async def delete_all_holdings(db: Session = Depends(get_db)):
    """
    Delete all mutual fund holdings, transactions, and assets.
    """
    try:
        service = MutualFundService(db)
        result = service.delete_all_holdings()
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to delete all holdings'))
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete all holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recalculate")
async def recalculate_holdings(db: Session = Depends(get_db)):
    """
    Recalculate all mutual fund holdings from transaction history.
    This will:
    - Recalculate invested_amount from buy/sell transactions
    - Update current_value from latest NAV
    - Calculate unrealized_gain and unrealized_gain_percentage
    """
    try:
        service = MutualFundService(db)
        result = service.recalculate_all_holdings()
        return result
        
    except Exception as e:
        logger.error(f"Failed to recalculate holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class UpdateHoldingRequest(BaseModel):
    invested_amount: Optional[float] = None
    units: Optional[float] = None


@router.patch("/holdings/{holding_id}")
async def update_holding(
    holding_id: str,
    request: UpdateHoldingRequest,
    db: Session = Depends(get_db)
):
    """
    Update a mutual fund holding's values.
    
    - **holding_id**: UUID of the holding to update
    - **invested_amount**: New invested amount (optional)
    - **units**: New units/quantity (optional)
    """
    try:
        service = MutualFundService(db)
        result = service.update_holding(
            holding_id=holding_id,
            invested_amount=request.invested_amount,
            units=request.units
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to update holding'))
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update holding: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-import-cas-json")
async def auto_import_cas_json(db: Session = Depends(get_db)):
    """
    Automatically import CAS data from the data/cas_api.json file.
    This endpoint is called on app initialization to load existing data.
    """
    try:
        import json
        from pathlib import Path
        from services.mutual_fund_service import MutualFundService
        from services.stock_service import StockService
        
        # Look for cas_api.json in data folder
        data_file = Path("data/cas_api.json")
        if not data_file.exists():
            # Try alternate path (from backend folder)
            data_file = Path("../data/cas_api.json")
        
        if not data_file.exists():
            logger.warning("No cas_api.json file found in data folder")
            return {
                'success': False,
                'message': 'No CAS JSON file found in data folder',
                'mutual_funds_imported': 0,
                'equities_imported': 0,
                'demat_mf_imported': 0
            }
        
        # Read and parse JSON
        with open(data_file, 'r', encoding='utf-8') as f:
            cas_data = json.load(f)
        
        logger.info(f"Auto-importing CAS data from {data_file}")
        
        mf_service = MutualFundService(db)
        stock_service = StockService(db)
        
        stats = {
            'mutual_funds_imported': 0,
            'equities_imported': 0,
            'demat_mf_imported': 0,
            'mf_transactions_imported': 0,
            'equity_transactions_imported': 0,
            'etf_transactions_imported': 0,
            'errors': []
        }
        
        # Import mutual funds
        if 'mutual_funds' in cas_data:
            logger.info(f"Found {len(cas_data['mutual_funds'])} mutual fund folios to import")
            for idx, folio in enumerate(cas_data['mutual_funds'], 1):
                amc = folio.get('amc', 'Unknown AMC')
                folio_number = folio.get('folio_number')
                
                logger.info(f"Processing folio {idx}: {amc} - {folio_number}")
                
                schemes = folio.get('schemes', [])
                logger.info(f"  Found {len(schemes)} schemes in this folio")
                
                for scheme_idx, scheme in enumerate(schemes, 1):
                    try:
                        scheme_name = scheme.get('name', 'Unknown')
                        scheme_isin = scheme.get('isin')
                        scheme_units = scheme.get('units', 0)
                        scheme_value = scheme.get('value', 0)
                        scheme_cost = scheme.get('cost')
                        scheme_nav = scheme.get('nav')
                        
                        # Extract gain information
                        gain_info = scheme.get('gain', {})
                        unrealized_gain = gain_info.get('absolute')
                        unrealized_gain_pct = gain_info.get('percentage')
                        
                        logger.info(f"  [{scheme_idx}] Importing: {scheme_name}")
                        logger.info(f"      ISIN: {scheme_isin}, Units: {scheme_units}, Value: {scheme_value}, Cost: {scheme_cost}")
                        logger.info(f"      Gain: {unrealized_gain}, Gain%: {unrealized_gain_pct}")
                        
                        # Add holding - Regular MF (not ETF)
                        result = mf_service.add_holding_from_cas(
                            isin=scheme_isin,
                            name=scheme_name,
                            units=scheme_units,
                            value=scheme_value,
                            cost=scheme_cost if scheme_cost else scheme_value,  # Use value as cost if cost not provided
                            folio_number=folio_number,
                            amc=amc,
                            nav=scheme_nav,
                            is_etf=False,  # Regular mutual fund
                            unrealized_gain=unrealized_gain,
                            unrealized_gain_pct=unrealized_gain_pct
                        )
                        
                        if result.get('success'):
                            stats['mutual_funds_imported'] += 1
                            logger.info(f"      ✓ Successfully imported")
                            
                            # Import transactions if available
                            transactions = scheme.get('transactions', [])
                            logger.info(f"      Importing {len(transactions)} transactions")
                            for txn in transactions:
                                try:
                                    mf_service.add_transaction_from_cas(
                                        asset_id=result.get('asset_id'),
                                        transaction_data=txn
                                    )
                                    stats['mf_transactions_imported'] += 1
                                except Exception as e:
                                    logger.warning(f"      Failed to import MF transaction: {e}")
                        else:
                            error_msg = result.get('error', 'Unknown error')
                            logger.error(f"      ✗ Failed to import: {error_msg}")
                            stats['errors'].append(f"Failed to import {scheme_name}: {error_msg}")
                            
                    except Exception as e:
                        logger.error(f"  ✗ Exception importing scheme {scheme.get('name')}: {e}")
                        logger.error(traceback.format_exc())
                        stats['errors'].append(f"Error importing {scheme.get('name')}: {str(e)}")
        
        # Import demat holdings
        if 'demat_accounts' in cas_data:
            for account in cas_data['demat_accounts']:
                dp_name = account.get('dp_name', 'Unknown DP')
                bo_id = account.get('bo_id')
                
                # Import equities
                for equity in account.get('holdings', {}).get('equities', []):
                    try:
                        result = stock_service.add_stock_from_cas(
                            isin=equity.get('isin'),
                            name=equity['name'],
                            units=equity.get('units', 0),
                            value=equity.get('value', 0),
                            symbol=equity.get('additional_info', {}).get('stock_symbol'),
                            dp_name=dp_name,
                            bo_id=bo_id
                        )
                        
                        if result.get('success'):
                            stats['equities_imported'] += 1
                            
                            # Import transactions
                            for txn in equity.get('transactions', []):
                                try:
                                    stock_service.add_transaction_from_cas(
                                        asset_id=result.get('asset_id'),
                                        transaction_data=txn
                                    )
                                    stats['equity_transactions_imported'] += 1
                                except Exception as e:
                                    logger.warning(f"Failed to import equity transaction: {e}")
                        else:
                            stats['errors'].append(f"Failed to import equity {equity['name']}")
                            
                    except Exception as e:
                        logger.error(f"Failed to import equity {equity.get('name')}: {e}")
                        stats['errors'].append(f"Error importing equity {equity.get('name')}: {str(e)}")
                
                # Import demat mutual funds (ETFs)
                for mf in account.get('holdings', {}).get('demat_mutual_funds', []):
                    try:
                        # Calculate invested amount from transactions using average cost method
                        transactions = mf.get('transactions', [])
                        invested_amount = 0.0
                        total_units = 0.0
                        
                        # Sort transactions by date to process chronologically
                        sorted_transactions = sorted(transactions, key=lambda x: x.get('date', ''))
                        
                        for txn in sorted_transactions:
                            txn_type = txn.get('type', '').upper()
                            txn_amount = float(txn.get('amount', 0) or 0)
                            txn_units = float(txn.get('units', 0) or 0)
                            
                            if 'PURCHASE' in txn_type or 'SIP' in txn_type:
                                # For purchases, add units and invested amount
                                total_units += txn_units
                                invested_amount += txn_amount
                            elif 'REDEMPTION' in txn_type or 'SELL' in txn_type:
                                # For redemptions, calculate average cost and reduce proportionally
                                if total_units > 0 and invested_amount > 0:
                                    avg_cost_per_unit = invested_amount / total_units
                                    invested_amount -= txn_units * avg_cost_per_unit
                                total_units -= txn_units
                                total_units = max(0, total_units)  # Ensure non-negative
                        
                        # Ensure invested_amount is non-negative
                        invested_amount = max(0.0, invested_amount)
                        
                        # Use calculated invested amount, or None if no transactions
                        cost = invested_amount if invested_amount > 0 and len(transactions) > 0 else None
                        
                        result = mf_service.add_holding_from_cas(
                            isin=mf.get('isin'),
                            name=mf['name'],
                            units=mf.get('units', 0),
                            value=mf.get('value', 0),
                            cost=cost,
                            folio_number=bo_id,
                            amc=dp_name,
                            nav=None,
                            is_etf=True
                        )
                        
                        if result.get('success'):
                            stats['demat_mf_imported'] += 1
                            
                            # Import transactions
                            for txn in transactions:
                                try:
                                    mf_service.add_transaction_from_cas(
                                        asset_id=result.get('asset_id'),
                                        transaction_data=txn
                                    )
                                    stats['etf_transactions_imported'] += 1
                                except Exception as e:
                                    logger.warning(f"Failed to import ETF transaction: {e}")
                            
                            # Recalculate invested amount from all transactions after import
                            try:
                                asset_id = result.get('asset_id')
                                if asset_id:
                                    recalculated = mf_service._calculate_invested_from_transactions(
                                        uuid.UUID(asset_id)
                                    )
                                    if recalculated > 0:
                                        # Update holding with recalculated invested amount
                                        holding = mf_service.db.query(Holding).filter(
                                            Holding.asset_id == uuid.UUID(asset_id),
                                            Holding.folio_number == bo_id
                                        ).first()
                                        if holding:
                                            holding.invested_amount = recalculated
                                            # Recalculate gains
                                            if holding.current_value:
                                                holding.unrealized_gain = float(holding.current_value) - recalculated
                                                holding.unrealized_gain_percentage = (
                                                    (float(holding.current_value) - recalculated) / recalculated * 100
                                                    if recalculated > 0 else 0
                                                )
                                            mf_service.db.commit()
                                            logger.info(f"Recalculated invested amount for {mf['name']}: {recalculated}")
                            except Exception as e:
                                logger.warning(f"Failed to recalculate invested amount: {e}")
                        else:
                            stats['errors'].append(f"Failed to import ETF {mf['name']}")
                            
                    except Exception as e:
                        logger.error(f"Failed to import demat MF {mf.get('name')}: {e}")
                        stats['errors'].append(f"Error importing ETF {mf.get('name')}: {str(e)}")
        
        logger.info(f"Auto-import completed: {stats}")
        stats['success'] = True
        stats['message'] = f"Successfully imported data from cas_api.json"
        return stats
        
    except Exception as e:
        logger.error(f"Auto-import failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'mutual_funds_imported': 0,
            'equities_imported': 0,
            'demat_mf_imported': 0
        }


@router.post("/import-cas-json")
async def import_cas_json(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import CAS data from JSON file.
    
    - **file**: CAS JSON file exported from CAS API
    """
    try:
        import json
        from services.mutual_fund_service import MutualFundService
        from services.stock_service import StockService
        
        # Validate file type
        if not file.filename.lower().endswith('.json'):
            raise HTTPException(status_code=400, detail="Only JSON files are allowed")
        
        # Read and parse JSON
        content = await file.read()
        cas_data = json.loads(content)
        
        logger.info(f"Importing CAS JSON data for {cas_data.get('investor', {}).get('name')}")
        
        mf_service = MutualFundService(db)
        stock_service = StockService(db)
        
        stats = {
            'mutual_funds_imported': 0,
            'equities_imported': 0,
            'demat_mf_imported': 0,
            'mf_transactions_imported': 0,
            'equity_transactions_imported': 0,
            'etf_transactions_imported': 0,
            'errors': []
        }
        
        # Import mutual funds
        if 'mutual_funds' in cas_data:
            for folio in cas_data['mutual_funds']:
                amc = folio.get('amc', 'Unknown AMC')
                folio_number = folio.get('folio_number')
                
                for scheme in folio.get('schemes', []):
                    try:
                        # Create or get asset
                        asset_data = {
                            'name': scheme['name'],
                            'isin': scheme.get('isin'),
                            'type': scheme.get('type', 'EQUITY'),
                            'amc': amc,
                            'folio_number': folio_number
                        }
                        
                        # Add holding
                        result = mf_service.add_holding_from_cas(
                            isin=scheme.get('isin'),
                            name=scheme['name'],
                            units=scheme.get('units', 0),
                            value=scheme.get('value', 0),
                            cost=scheme.get('cost', 0),
                            folio_number=folio_number,
                            amc=amc,
                            nav=scheme.get('nav')
                        )
                        
                        if result.get('success'):
                            stats['mutual_funds_imported'] += 1
                            
                            # Import transactions if available
                            for txn in scheme.get('transactions', []):
                                try:
                                    mf_service.add_transaction_from_cas(
                                        asset_id=result.get('asset_id'),
                                        transaction_data=txn
                                    )
                                    stats['mf_transactions_imported'] += 1
                                except Exception as e:
                                    logger.warning(f"Failed to import MF transaction: {e}")
                        else:
                            stats['errors'].append(f"Failed to import {scheme['name']}")
                            
                    except Exception as e:
                        logger.error(f"Failed to import scheme {scheme.get('name')}: {e}")
                        stats['errors'].append(f"Error importing {scheme.get('name')}: {str(e)}")
        
        # Import demat holdings
        if 'demat_accounts' in cas_data:
            for account in cas_data['demat_accounts']:
                dp_name = account.get('dp_name', 'Unknown DP')
                bo_id = account.get('bo_id')
                
                # Import equities
                for equity in account.get('holdings', {}).get('equities', []):
                    try:
                        result = stock_service.add_stock_from_cas(
                            isin=equity.get('isin'),
                            name=equity['name'],
                            units=equity.get('units', 0),
                            value=equity.get('value', 0),
                            symbol=equity.get('additional_info', {}).get('stock_symbol'),
                            dp_name=dp_name,
                            bo_id=bo_id
                        )
                        
                        if result.get('success'):
                            stats['equities_imported'] += 1
                            
                            # Import transactions
                            for txn in equity.get('transactions', []):
                                try:
                                    stock_service.add_transaction_from_cas(
                                        asset_id=result.get('asset_id'),
                                        transaction_data=txn
                                    )
                                    stats['equity_transactions_imported'] += 1
                                except Exception as e:
                                    logger.warning(f"Failed to import equity transaction: {e}")
                        else:
                            stats['errors'].append(f"Failed to import equity {equity['name']}")
                            
                    except Exception as e:
                        logger.error(f"Failed to import equity {equity.get('name')}: {e}")
                        stats['errors'].append(f"Error importing equity {equity.get('name')}: {str(e)}")
                
                # Import demat mutual funds (ETFs)
                for mf in account.get('holdings', {}).get('demat_mutual_funds', []):
                    try:
                        # Calculate invested amount from transactions using average cost method
                        transactions = mf.get('transactions', [])
                        invested_amount = 0.0
                        total_units = 0.0
                        
                        # Sort transactions by date to process chronologically
                        sorted_transactions = sorted(transactions, key=lambda x: x.get('date', ''))
                        
                        for txn in sorted_transactions:
                            txn_type = txn.get('type', '').upper()
                            txn_amount = float(txn.get('amount', 0) or 0)
                            txn_units = float(txn.get('units', 0) or 0)
                            
                            if 'PURCHASE' in txn_type or 'SIP' in txn_type:
                                # For purchases, add units and invested amount
                                total_units += txn_units
                                invested_amount += txn_amount
                            elif 'REDEMPTION' in txn_type or 'SELL' in txn_type:
                                # For redemptions, calculate average cost and reduce proportionally
                                if total_units > 0 and invested_amount > 0:
                                    avg_cost_per_unit = invested_amount / total_units
                                    invested_amount -= txn_units * avg_cost_per_unit
                                total_units -= txn_units
                                total_units = max(0, total_units)  # Ensure non-negative
                        
                        # Ensure invested_amount is non-negative
                        invested_amount = max(0.0, invested_amount)
                        
                        # Use calculated invested amount, or None if no transactions
                        cost = invested_amount if invested_amount > 0 and len(transactions) > 0 else None
                        
                        result = mf_service.add_holding_from_cas(
                            isin=mf.get('isin'),
                            name=mf['name'],
                            units=mf.get('units', 0),
                            value=mf.get('value', 0),
                            cost=cost,
                            folio_number=bo_id,
                            amc=dp_name,
                            nav=None,
                            is_etf=True
                        )
                        
                        if result.get('success'):
                            stats['demat_mf_imported'] += 1
                            
                            # Import transactions
                            for txn in transactions:
                                try:
                                    mf_service.add_transaction_from_cas(
                                        asset_id=result.get('asset_id'),
                                        transaction_data=txn
                                    )
                                    stats['etf_transactions_imported'] += 1
                                except Exception as e:
                                    logger.warning(f"Failed to import ETF transaction: {e}")
                            
                            # Recalculate invested amount from all transactions after import
                            try:
                                asset_id = result.get('asset_id')
                                if asset_id:
                                    recalculated = mf_service._calculate_invested_from_transactions(
                                        uuid.UUID(asset_id)
                                    )
                                    if recalculated > 0:
                                        # Update holding with recalculated invested amount
                                        holding = mf_service.db.query(Holding).filter(
                                            Holding.asset_id == uuid.UUID(asset_id),
                                            Holding.folio_number == bo_id
                                        ).first()
                                        if holding:
                                            holding.invested_amount = recalculated
                                            # Recalculate gains
                                            if holding.current_value:
                                                holding.unrealized_gain = float(holding.current_value) - recalculated
                                                holding.unrealized_gain_percentage = (
                                                    (float(holding.current_value) - recalculated) / recalculated * 100
                                                    if recalculated > 0 else 0
                                                )
                                            mf_service.db.commit()
                                            logger.info(f"Recalculated invested amount for {mf['name']}: {recalculated}")
                            except Exception as e:
                                logger.warning(f"Failed to recalculate invested amount: {e}")
                        else:
                            stats['errors'].append(f"Failed to import ETF {mf['name']}")
                            
                    except Exception as e:
                        logger.error(f"Failed to import demat MF {mf.get('name')}: {e}")
                        stats['errors'].append(f"Error importing ETF {mf.get('name')}: {str(e)}")
        
        logger.info(f"CAS JSON import completed: {stats}")
        return stats
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON file: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON file: {str(e)}")
    except Exception as e:
        logger.error(f"CAS JSON import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()
