"""
TradingXtra — Database Layer
PostgreSQL connection, ORM models, session management.
"""

import os
import logging
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Connection Setup ────────────────────────────────────────────────
import socket

def _resolve_database_url() -> str:
    url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:54322/postgres",
    )
    try:
        parts = url.split("@")
        if len(parts) > 1:
            credentials = parts[0]
            host_and_db = parts[1].split("/")
            host_port = host_and_db[0]
            db_path = "/".join(host_and_db[1:]) if len(host_and_db) > 1 else ""
            
            if ":" in host_port:
                host, port_str = host_port.split(":")
                if port_str == "6543":
                    logger.info(f"Checking database connection to {host}:6543...")
                    try:
                        # Short timeout (3s) to check port availability
                        with socket.create_connection((host, 6543), timeout=3.0):
                            logger.info(f"✓ Database host {host}:6543 is reachable.")
                            return url
                    except Exception as e:
                        logger.warning(
                            f"✗ Connection to port 6543 failed: {e}. "
                            "Port 6543 might be blocked in this environment (e.g. Render). "
                            "Falling back to port 5432 (Session Mode)..."
                        )
                        new_host_port = f"{host}:5432"
                        return f"{credentials}@{new_host_port}/{db_path}"
    except Exception as parse_err:
        logger.error(f"Error parsing DATABASE_URL: {parse_err}")
    return url

DATABASE_URL = _resolve_database_url()

# PostgreSQL with production-ready pool settings
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,       # Detect dead connections before use
    pool_size=5,              # Keep 5 connections in the pool
    max_overflow=10,          # Allow 10 extra connections under load
    pool_recycle=300,         # Recycle connections every 5 min (PgBouncer/Supabase may drop idle)
    pool_timeout=30,          # Wait up to 30s for a free connection
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── ORM Model ───────────────────────────────────────────────────────
class OHLCVData(Base):
    """Daily OHLCV price data."""

    __tablename__ = "ohlcv_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)

    __table_args__ = (
        UniqueConstraint("symbol", "timestamp", name="uq_ohlcv_symbol_ts"),
        Index("idx_ohlcv_symbol", "symbol"),
        Index("idx_ohlcv_symbol_ts", "symbol", "timestamp"),
    )

    def __repr__(self):
        return f"<OHLCV {self.symbol} {self.timestamp} C={self.close}>"


class FetchTracker(Base):
    """Tracks when each symbol was last fetched from yfinance.
    Persists across server restarts for smart preloading."""

    __tablename__ = "fetch_tracker"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    last_fetched_at = Column(DateTime)
    rows_fetched = Column(Integer, default=0)

    def __repr__(self):
        return f"<Fetch {self.symbol} @ {self.last_fetched_at}>"


from sqlalchemy import JSON

class InvestSmartCache(Base):
    """Caches the Gemini analysis of YouTube videos."""
    
    __tablename__ = "invest_smart_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_link = Column(String(255), unique=True, nullable=False, index=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON, nullable=False)

    def __repr__(self):
        return f"<InvestSmartCache {self.video_link} @ {self.analyzed_at}>"


class MarketBriefCache(Base):
    """Persists the daily market brief so dashboards load instantly.
    One row per calendar date — overwritten when refreshed."""

    __tablename__ = "market_brief_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_date = Column(String(10), unique=True, nullable=False, index=True)  # 'YYYY-MM-DD'
    brief_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<MarketBriefCache {self.cache_date} @ {self.created_at}>"


class Trade(Base):
    """Trade journal — tracks all decisions and their outcomes."""

    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    decision = Column(String(10), nullable=False)  # ACCEPT / REJECT
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(10), default="OPEN")  # OPEN / CLOSED
    exit_price = Column(Float, nullable=True)
    exit_timestamp = Column(DateTime, nullable=True)
    outcome = Column(String(10), nullable=True)  # WIN / LOSS / None
    pnl = Column(Float, nullable=True)  # ₹ per share
    pnl_pct = Column(Float, nullable=True)  # % return
    mfe = Column(Float, default=0.0)  # Max Favorable Excursion
    mae = Column(Float, default=0.0)  # Max Adverse Excursion

    # Phase 3 calibration fields
    predicted_probability = Column(Float, nullable=True)
    predicted_ev = Column(Float, nullable=True)
    actual_result = Column(Float, nullable=True)  # 1.0 = win, 0.0 = loss
    regime_at_entry = Column(String(20), nullable=True)
    score_at_entry = Column(Float, nullable=True)

    # Phase 3.5 execution realism
    position_size = Column(Float, nullable=True)  # Number of shares
    capital_at_entry = Column(Float, nullable=True)  # Capital when trade opened
    slippage_applied = Column(Float, default=0.002)  # Slippage % used

    __table_args__ = (
        Index("idx_trades_symbol_status", "symbol", "status"),
        Index("idx_trades_status", "status"),
    )

    def __repr__(self):
        return f"<Trade {self.symbol} {self.status} {self.outcome}>"


# ── Helpers ──────────────────────────────────────────────────────────
def init_db():
    """Create all tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def get_db():
    """FastAPI dependency — yields a DB session, auto-closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
