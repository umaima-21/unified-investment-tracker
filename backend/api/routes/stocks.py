"""
Stocks API Routes.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from loguru import logger

from database import get_db
from services.stock_service import StockService


router = APIRouter()


class AddStockRequest(BaseModel):
    symbol: str
    name: str
    quantity: float
    invested_amount: float
    exchange: str = "NSE"
    isin: Optional[str] = None


@router.get("/holdings", response_model=List[dict])
async def get_stock_holdings(db: Session = Depends(get_db)):
    """
    Get all stock holdings.
    """
    try:
        service = StockService(db)
        holdings = service.get_all_holdings()
        return holdings
    except Exception as e:
        logger.error(f"Failed to get stock holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/add", response_model=dict)
async def add_stock(
    request: AddStockRequest,
    db: Session = Depends(get_db)
):
    """
    Manually add a stock holding.
    """
    try:
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than 0")
        
        if request.invested_amount <= 0:
            raise HTTPException(status_code=400, detail="Invested amount must be greater than 0")
        
        service = StockService(db)
        result = service.add_stock_manually(
            symbol=request.symbol,
            name=request.name,
            quantity=request.quantity,
            invested_amount=request.invested_amount,
            exchange=request.exchange,
            isin=request.isin
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to add stock'))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add stock: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/update-prices", response_model=dict)
async def update_stock_prices(
    symbols: Optional[List[str]] = None,
    db: Session = Depends(get_db)
):
    """
    Update stock prices.
    
    - **symbols**: Optional list of stock symbols to update. If not provided, updates all.
    """
    try:
        service = StockService(db)
        result = service.update_prices(symbols)
        return result
    except Exception as e:
        logger.error(f"Failed to update stock prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync", response_model=dict)
async def sync_stock_holdings(db: Session = Depends(get_db)):
    """
    Sync stock holdings from ICICIdirect (if configured).
    """
    try:
        service = StockService(db)
        result = service.sync_holdings()
        return result
    except Exception as e:
        logger.error(f"Failed to sync stock holdings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

