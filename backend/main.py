"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from config.settings import settings
from database import Base, engine

# Configure logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.LOG_LEVEL,
)

# Create FastAPI application
app = FastAPI(
    title="Unified Investment Tracker API",
    description="API for tracking mutual funds, stocks, crypto, and fixed deposits",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Unified Investment Tracker API")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    
    # Create all database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.success("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    # Start scheduler if auto updates are enabled
    if settings.ENABLE_AUTO_UPDATES:
        try:
            from schedulers.scheduler import setup_scheduler
            app.state.scheduler = setup_scheduler()
            app.state.scheduler.start()
            logger.success("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            # Don't raise - allow app to start without scheduler


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down Unified Investment Tracker API")
    
    # Shutdown scheduler if running
    try:
        if hasattr(app.state, 'scheduler') and app.state.scheduler:
            app.state.scheduler.shutdown()
            logger.info("Scheduler shutdown")
    except Exception as e:
        logger.warning(f"Error shutting down scheduler: {e}")


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "message": "Unified Investment Tracker API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/api/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
    }


# Import and include routers
from api.routes import (
    mutual_funds,
    assets,
    holdings,
    transactions,
    portfolio,
    crypto,
    stocks,
    fixed_deposits,
    ppf_accounts,
    epf_accounts,
    us_stocks,
    liquid,
    admin_migration,
    unlisted_shares,
    insurance,
    other_assets
)

app.include_router(mutual_funds.router, prefix="/api/mutual-funds", tags=["Mutual Funds"])
app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
app.include_router(holdings.router, prefix="/api/holdings", tags=["Holdings"])
app.include_router(transactions.router, prefix="/api/transactions", tags=["Transactions"])

# Debug router
from api.routes import debug_bandhan
app.include_router(debug_bandhan.router, prefix="/api", tags=["Debug"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(crypto.router, prefix="/api/crypto", tags=["Crypto"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["Stocks"])
app.include_router(fixed_deposits.router, prefix="/api/fixed-deposits", tags=["Fixed Deposits"])
app.include_router(ppf_accounts.router, prefix="/api/ppf-accounts", tags=["PPF Accounts"])
app.include_router(epf_accounts.router, prefix="/api/epf-accounts", tags=["EPF Accounts"])
app.include_router(us_stocks.router, prefix="/api/us-stocks", tags=["US Stocks"])
app.include_router(unlisted_shares.router, prefix="/api/unlisted-shares", tags=["Unlisted Shares"])
app.include_router(liquid.router, prefix="/api/liquid", tags=["Liquid"])
app.include_router(insurance.router, prefix="/api/insurance", tags=["Insurance"])
app.include_router(other_assets.router, prefix="/api/other-assets", tags=["Other Assets"])
app.include_router(admin_migration.router, tags=["Admin"])


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.APP_HOST}:{settings.APP_PORT}")
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_ENV == "development",
    )
