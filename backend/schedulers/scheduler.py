"""
Scheduler setup for automated daily updates.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from config.settings import settings
from schedulers.daily_updates import (
    update_mf_navs,
    update_stock_prices,
    update_crypto_prices,
    sync_crypto_holdings,
    refresh_holdings,
    update_fd_values,
    create_portfolio_snapshot
)


def setup_scheduler() -> BackgroundScheduler:
    """
    Setup and configure the scheduler.
    
    Returns:
        Configured scheduler instance
    """
    scheduler = BackgroundScheduler()
    
    if not settings.ENABLE_AUTO_UPDATES:
        logger.info("Auto updates are disabled in settings")
        return scheduler
    
    # Parse schedule times (format: "HH:MM")
    def parse_time(time_str: str) -> tuple:
        parts = time_str.split(":")
        return int(parts[0]), int(parts[1])
    
    # Schedule MF NAV updates
    mf_hour, mf_minute = parse_time(settings.SCHEDULE_MF_NAV_TIME)
    scheduler.add_job(
        update_mf_navs,
        trigger=CronTrigger(hour=mf_hour, minute=mf_minute),
        id='update_mf_navs',
        name='Update Mutual Fund NAVs',
        replace_existing=True
    )
    logger.info(f"Scheduled MF NAV updates at {settings.SCHEDULE_MF_NAV_TIME}")
    
    # Schedule stock price updates
    stock_hour, stock_minute = parse_time(settings.SCHEDULE_STOCK_PRICE_TIME)
    scheduler.add_job(
        update_stock_prices,
        trigger=CronTrigger(hour=stock_hour, minute=stock_minute),
        id='update_stock_prices',
        name='Update Stock Prices',
        replace_existing=True
    )
    logger.info(f"Scheduled stock price updates at {settings.SCHEDULE_STOCK_PRICE_TIME}")
    
    # Schedule crypto price updates
    crypto_hour, crypto_minute = parse_time(settings.SCHEDULE_CRYPTO_PRICE_TIME)
    scheduler.add_job(
        update_crypto_prices,
        trigger=CronTrigger(hour=crypto_hour, minute=crypto_minute),
        id='update_crypto_prices',
        name='Update Crypto Prices',
        replace_existing=True
    )
    logger.info(f"Scheduled crypto price updates at {settings.SCHEDULE_CRYPTO_PRICE_TIME}")
    
    # Schedule crypto holdings sync (after price update)
    scheduler.add_job(
        sync_crypto_holdings,
        trigger=CronTrigger(hour=crypto_hour, minute=crypto_minute + 5),
        id='sync_crypto_holdings',
        name='Sync Crypto Holdings',
        replace_existing=True
    )
    
    # Schedule holdings refresh (after all price updates)
    portfolio_hour, portfolio_minute = parse_time(settings.SCHEDULE_PORTFOLIO_UPDATE_TIME)
    scheduler.add_job(
        refresh_holdings,
        trigger=CronTrigger(hour=portfolio_hour, minute=portfolio_minute),
        id='refresh_holdings',
        name='Refresh Holdings',
        replace_existing=True
    )
    logger.info(f"Scheduled holdings refresh at {settings.SCHEDULE_PORTFOLIO_UPDATE_TIME}")
    
    # Schedule FD value updates
    scheduler.add_job(
        update_fd_values,
        trigger=CronTrigger(hour=portfolio_hour, minute=portfolio_minute),
        id='update_fd_values',
        name='Update FD Values',
        replace_existing=True
    )
    
    # Schedule portfolio snapshot (after holdings refresh)
    scheduler.add_job(
        create_portfolio_snapshot,
        trigger=CronTrigger(hour=portfolio_hour, minute=portfolio_minute + 5),
        id='create_portfolio_snapshot',
        name='Create Portfolio Snapshot',
        replace_existing=True
    )
    
    return scheduler

