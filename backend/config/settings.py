"""
Application configuration management using Pydantic Settings.
Loads configuration from environment variables.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "investment_tracker"
    DB_USER: str = "postgres"
    DB_PASSWORD: str
    
    # Application Configuration
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    
    # Mutual Funds APIs
    MFAPI_BASE_URL: str = "https://api.mfapi.in"
    
    # ICICI Direct API
    ICICIDIRECT_API_KEY: Optional[str] = None
    ICICIDIRECT_API_SECRET: Optional[str] = None
    ICICIDIRECT_USER_ID: Optional[str] = None
    ICICIDIRECT_PASSWORD: Optional[str] = None
    ICICIDIRECT_BASE_URL: str = "https://api.icicidirect.com"
    
    # CoinDCX API
    COINDCX_API_KEY: Optional[str] = None
    COINDCX_API_SECRET: Optional[str] = None
    COINDCX_BASE_URL: str = "https://api.coindcx.com"
    
    # Optional APIs
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    NSE_API_KEY: Optional[str] = None
    
    # OpenAI Configuration (for CAS parsing)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"  # Can use "gpt-4o" for better accuracy
    
    # Google Gemini Configuration (for CAS parsing)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3-flash-preview"  # Gemini 3.0 Flash Preview
    
    @property
    def openai_model_validated(self) -> str:
        """Return a valid OpenAI model name."""
        valid_models = ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
        if self.OPENAI_MODEL in valid_models:
            return self.OPENAI_MODEL
        # Default to gpt-4o-mini if invalid model specified
        return "gpt-4o-mini"
    
    # Scheduler Configuration
    SCHEDULE_MF_NAV_TIME: str = "20:00"
    SCHEDULE_STOCK_PRICE_TIME: str = "18:00"
    SCHEDULE_CRYPTO_PRICE_TIME: str = "21:00"
    SCHEDULE_PORTFOLIO_UPDATE_TIME: str = "22:00"
    ENABLE_AUTO_UPDATES: bool = True
    
    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # URLs
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    
    @property
    def database_url(self) -> str:
        """Construct PostgreSQL database URL."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def async_database_url(self) -> str:
        """Construct async PostgreSQL database URL."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        # Look for .env in project root (parent of backend directory)
        # Try multiple locations
        _project_root = Path(__file__).parent.parent.parent
        _env_file = _project_root / ".env"
        
        if _env_file.exists():
            env_file = str(_env_file)
        else:
            # Fallback to current directory or parent
            _parent_env = Path(__file__).parent.parent / ".env"
            if _parent_env.exists():
                env_file = str(_parent_env)
            else:
                env_file = ".env"
        
        env_file_encoding = "utf-8"
        case_sensitive = True


# Create global settings instance
settings = Settings()
