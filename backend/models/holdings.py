"""
Holdings Model - Stores current investment holdings.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database.base import Base


class Holding(Base):
    """
    Holdings Table.
    
    Stores current holdings for each asset with quantity and valuation.
    This is an aggregated view updated from transactions.
    """
    
    __tablename__ = "holdings"
    
    holding_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(UUID(as_uuid=True), ForeignKey("assets_master.asset_id"), nullable=False, index=True)  # Removed unique=True to allow multiple holdings per asset
    
    # Holding details
    folio_number = Column(String(100), nullable=True)  # For mutual funds - folio number
    quantity = Column(Numeric(18, 6), nullable=False, default=0)  # Units/shares held
    invested_amount = Column(Numeric(18, 2), nullable=False, default=0)  # Total invested
    avg_price = Column(Numeric(18, 6), nullable=True)  # Average purchase price
    current_value = Column(Numeric(18, 2), nullable=True)  # Current market value
    
    # Calculated fields (updated by portfolio engine)
    unrealized_gain = Column(Numeric(18, 2), nullable=True)  # current_value - invested_amount
    unrealized_gain_percentage = Column(Numeric(8, 2), nullable=True)  # (gain / invested) * 100
    annualized_return = Column(Numeric(8, 2), nullable=True)  # Annualized return percentage from CAS
    
    # Timestamps
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    asset = relationship("Asset", back_populates="holdings")
    
    def __repr__(self):
        return f"<Holding(asset_id={self.asset_id}, quantity={self.quantity}, value={self.current_value})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "holding_id": str(self.holding_id),
            "asset_id": str(self.asset_id),
            "folio_number": self.folio_number,
            "quantity": float(self.quantity) if self.quantity else 0,
            "invested_amount": float(self.invested_amount) if self.invested_amount else 0,
            "avg_price": float(self.avg_price) if self.avg_price else None,
            "current_value": float(self.current_value) if self.current_value else None,
            "unrealized_gain": float(self.unrealized_gain) if self.unrealized_gain else None,
            "unrealized_gain_percentage": float(self.unrealized_gain_percentage) if self.unrealized_gain_percentage else None,
            "annualized_return": float(self.annualized_return) if self.annualized_return else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
