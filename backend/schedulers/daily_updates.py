"""
Daily update jobs for automated portfolio updates.
"""

from datetime import datetime, time
from loguru import logger
from sqlalchemy.orm import Session

from database import SessionLocal
from services.mutual_fund_service import MutualFundService
from services.crypto_service import CryptoService
from services.stock_service import StockService
from services.fd_service import FixedDepositService
from services.portfolio_service import PortfolioService
from config.settings import settings


def update_mf_navs():
    """Update mutual fund NAVs."""
    logger.info("Starting MF NAV update job")
    db: Session = SessionLocal()
    try:
        service = MutualFundService(db)
        result = service.update_nav_prices()
        logger.success(f"MF NAV update complete: {result}")
    except Exception as e:
        logger.error(f"MF NAV update failed: {e}")
    finally:
        db.close()


def update_stock_prices():
    """Update stock prices."""
    logger.info("Starting stock price update job")
    db: Session = SessionLocal()
    try:
        service = StockService(db)
        result = service.update_prices()
        logger.success(f"Stock price update complete: {result}")
    except Exception as e:
        logger.error(f"Stock price update failed: {e}")
    finally:
        db.close()


def update_crypto_prices():
    """Update crypto prices."""
    logger.info("Starting crypto price update job")
    db: Session = SessionLocal()
    try:
        service = CryptoService(db)
        result = service.update_prices()
        logger.success(f"Crypto price update complete: {result}")
    except Exception as e:
        logger.error(f"Crypto price update failed: {e}")
    finally:
        db.close()


def sync_crypto_holdings():
    """Sync crypto holdings from CoinDCX."""
    logger.info("Starting crypto holdings sync job")
    db: Session = SessionLocal()
    try:
        service = CryptoService(db)
        result = service.sync_holdings()
        logger.success(f"Crypto holdings sync complete: {result}")
    except Exception as e:
        logger.error(f"Crypto holdings sync failed: {e}")
    finally:
        db.close()


def refresh_holdings():
    """Refresh all holdings from transactions."""
    logger.info("Starting holdings refresh job")
    db: Session = SessionLocal()
    try:
        service = PortfolioService(db)
        result = service.refresh_holdings()
        logger.success(f"Holdings refresh complete: {result}")
    except Exception as e:
        logger.error(f"Holdings refresh failed: {e}")
    finally:
        db.close()


def update_fd_values():
    """Update fixed deposit values."""
    logger.info("Starting FD value update job")
    db: Session = SessionLocal()
    try:
        service = FixedDepositService(db)
        result = service.update_fd_values()
        logger.success(f"FD value update complete: {result}")
    except Exception as e:
        logger.error(f"FD value update failed: {e}")
    finally:
        db.close()


def create_portfolio_snapshot():
    """Create daily portfolio snapshot."""
    logger.info("Starting portfolio snapshot job")
    db: Session = SessionLocal()
    try:
        service = PortfolioService(db)
        result = service.create_portfolio_snapshot()
        logger.success(f"Portfolio snapshot complete: {result}")
    except Exception as e:
        logger.error(f"Portfolio snapshot failed: {e}")
    finally:
        db.close()


def run_daily_updates():
    """
    Run all daily update jobs in sequence.
    This is the main function called by the scheduler.
    """
    logger.info("=" * 50)
    logger.info("Starting daily portfolio updates")
    logger.info("=" * 50)
    
    # 1. Update prices
    update_mf_navs()
    update_stock_prices()
    update_crypto_prices()
    
    # 2. Sync holdings (for crypto)
    sync_crypto_holdings()
    
    # 3. Update FD values
    update_fd_values()
    
    # 4. Refresh all holdings
    refresh_holdings()
    
    # 5. Create portfolio snapshot
    create_portfolio_snapshot()
    
    logger.info("=" * 50)
    logger.info("Daily portfolio updates complete")
    logger.info("=" * 50)

