"""
Prices Model - Stores daily prices for all assets.
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, Numeric, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.base import Base


class Price(Base):
    """
    Prices Table.
    
    Stores daily prices (NAV/close price) for all assets.
    Used for portfolio valuation and performance calculations.
    """
    
    __tablename__ = "prices"
    
    price_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets_master.asset_id"), nullable=False, index=True)
    
    # Price details
    price_date = Column(Date, nullable=False, index=True)
    price = Column(Numeric(18, 6), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    asset = relationship("Asset", back_populates="prices")
    
    # Unique constraint: one price per asset per day
    __table_args__ = (
        UniqueConstraint('asset_id', 'price_date', name='uix_asset_price_date'),
    )
    
    def __repr__(self):
        return f"<Price(asset_id={self.asset_id}, date={self.price_date}, price={self.price})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "price_id": str(self.price_id),
            "asset_id": str(self.asset_id),
            "price_date": self.price_date.isoformat() if isinstance(self.price_date, date) else self.price_date,
            "price": float(self.price) if self.price else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
