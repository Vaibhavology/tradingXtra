"""Configuration from environment variables"""

import os
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Settings:
    # API Settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # CORS
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    
    # Data source (for future live data)
    DATA_SOURCE: str = os.getenv("DATA_SOURCE", "mock")  # mock, truedata, dhan, etc.
    
    # Twitter API (for future integration)
    TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
    TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
    
    # Gate thresholds (LOCKED - these define momentum trading)
    MOMENTUM_MIN_MOVE: float = 4.0  # Minimum % move in 5-10 sessions
    VOLUME_MIN_MULTIPLE: float = 1.5  # Minimum volume vs 20-day avg
    SECTOR_MIN_OUTPERFORMANCE: float = 0.5  # Sector must beat NIFTY by this %
    
    # Scoring weights (LOCKED)
    WEIGHT_MOMENTUM: float = 0.25
    WEIGHT_VOLUME: float = 0.20
    WEIGHT_SECTOR: float = 0.15
    WEIGHT_TECHNICAL: float = 0.15
    WEIGHT_FLOW: float = 0.10
    WEIGHT_TWITTER: float = 0.10
    WEIGHT_NEWS: float = 0.05

settings = Settings()
