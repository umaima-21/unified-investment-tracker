"""
Portfolio Snapshot Model - Stores daily portfolio summary.
"""

import uuid
from datetime import datetime, date
from sqlalchemy import Column, Numeric, Date, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

from database.base import Base


class PortfolioSnapshot(Base):
    """
    Portfolio Snapshot Table.
    
    Stores daily aggregated portfolio metrics.
    Used for historical performance tracking and dashboard charts.
    """
    
    __tablename__ = "portfolio_snapshot"
    
    snapshot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_date = Column(Date, nullable=False, unique=True, index=True)
    
    # Portfolio metrics
    total_invested = Column(Numeric(18, 2), nullable=False, default=0)
    total_current_value = Column(Numeric(18, 2), nullable=False, default=0)
    total_returns = Column(Numeric(18, 2), nullable=False, default=0)  # Absolute returns
    returns_percentage = Column(Numeric(8, 2), nullable=False, default=0)
    
    # Asset allocation (stored as JSON)
    # Format: {"MF": 45.5, "STOCK": 30.2, "CRYPTO": 14.3, "FD": 10.0}
    asset_allocation = Column(JSONB, nullable=True)
    
    # Additional metrics
    # Format: {"xirr": 12.5, "day_change": 1500.50, "day_change_pct": 0.75}
    metrics = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<PortfolioSnapshot(date={self.snapshot_date}, value={self.total_current_value})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "snapshot_id": str(self.snapshot_id),
            "snapshot_date": self.snapshot_date.isoformat() if isinstance(self.snapshot_date, date) else self.snapshot_date,
            "total_invested": float(self.total_invested) if self.total_invested else 0,
            "total_current_value": float(self.total_current_value) if self.total_current_value else 0,
            "total_returns": float(self.total_returns) if self.total_returns else 0,
            "returns_percentage": float(self.returns_percentage) if self.returns_percentage else 0,
            "asset_allocation": self.asset_allocation,
            "metrics": self.metrics,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
