"""
TradingXtra Phase 1 — Database Layer
PostgreSQL connection, ORM model, session management.

For quick testing without PostgreSQL, set:
  DATABASE_URL=sqlite:///./tradingxtra.db
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
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/tradingxtra",
)

# Detect SQLite for compatibility (no pool_pre_ping on SQLite)
_is_sqlite = DATABASE_URL.startswith("sqlite")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=not _is_sqlite,
    # SQLite needs check_same_thread=False for FastAPI
    connect_args={"check_same_thread": False} if _is_sqlite else {},
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
