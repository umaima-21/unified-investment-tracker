"""Debug endpoint to check Bandhan holdings."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.assets import Asset
from models.holdings import Holding
from loguru import logger

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/bandhan")
async def debug_bandhan(db: Session = Depends(get_db)):
    """Check all Bandhan holdings in the database."""
    
    # Find Bandhan asset
    bandhan_assets = db.query(Asset).filter(
        Asset.isin == 'INF194K01391'
    ).all()
    
    result = {
        "assets_found": len(bandhan_assets),
        "assets": [],
        "holdings": []
    }
    
    for asset in bandhan_assets:
        result["assets"].append({
            "asset_id": str(asset.asset_id),
            "name": asset.name,
            "isin": asset.isin,
            "amc": asset.amc,
            "asset_type": asset.asset_type
        })
        
        # Get holdings for this asset
        holdings = db.query(Holding).filter(
            Holding.asset_id == asset.asset_id
        ).all()
        
        for h in holdings:
            result["holdings"].append({
                "holding_id": str(h.holding_id),
                "asset_id": str(h.asset_id),
                "folio_number": h.folio_number,
                "quantity": float(h.quantity) if h.quantity else 0,
                "invested_amount": float(h.invested_amount) if h.invested_amount else 0,
                "current_value": float(h.current_value) if h.current_value else 0,
                "unrealized_gain": float(h.unrealized_gain) if h.unrealized_gain else 0
            })
    
    return result

