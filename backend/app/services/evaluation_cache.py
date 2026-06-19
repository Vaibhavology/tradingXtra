"""
Evaluation Cache — 3-tier caching for pre-computed stock evaluations.

Tier 1: In-memory dict (< 1ms, TTL 5 min)
Tier 2: Database ScanResult table (< 50ms, TTL 30 min)
Tier 3: Live evaluation (200ms-2s, on-demand)

Background batch jobs populate tiers 1 & 2 so user API calls
almost never hit tier 3.
"""

import json
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine

logger = logging.getLogger(__name__)

# ── ORM Model ────────────────────────────────────────────────────────

class ScanResult(Base):
    """Persisted stock evaluation result. Survives server restarts."""

    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    evaluated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    decision = Column(String(10), nullable=False)       # ACCEPT / REJECT / ERROR
    score = Column(Float, default=0.0)
    probability = Column(Float, default=0.0)
    ev = Column(Float, default=0.0)
    entry_price = Column(Float, default=0.0)
    stop_loss = Column(Float, default=0.0)
    target_price = Column(Float, default=0.0)
    atr = Column(Float, default=0.0)
    reward_risk = Column(Float, default=0.0)
    result_json = Column(Text, nullable=False)           # Full result dict as JSON
    priority_score = Column(Float, default=0.0)          # For scheduling

    __table_args__ = (
        Index("idx_scan_decision", "decision"),
        Index("idx_scan_eval_time", "evaluated_at"),
    )

    def __repr__(self):
        return f"<ScanResult {self.symbol} {self.decision} @ {self.evaluated_at}>"




# ── In-Memory Cache (Tier 1) ────────────────────────────────────────

_mem_cache: Dict[str, Dict] = {}      # symbol → {result, ts}
_scan_cache: Dict[str, Any] = {}      # "all_results" → {data, ts}
_cache_lock = threading.Lock()

# TTL settings (seconds)
TTL_SINGLE = 300     # 5 min for individual stock
TTL_SCAN = 300       # 5 min for full scan results
TTL_DB = 14400       # 4 hours — DB results survive restarts, batch keeps them fresh


def get_cached_result(symbol: str) -> Optional[Dict]:
    """
    3-tier lookup: memory → DB → None.
    Returns the evaluation result dict or None if stale/missing.
    """
    symbol = symbol.upper()

    # ── Tier 1: Memory ───────────────────────────────────────────
    with _cache_lock:
        entry = _mem_cache.get(symbol)
        if entry and (time.time() - entry["ts"]) < TTL_SINGLE:
            return entry["result"]

    # ── Tier 2: Database ─────────────────────────────────────────
    db = SessionLocal()
    try:
        row = db.query(ScanResult).filter(ScanResult.symbol == symbol).first()
        if row and row.evaluated_at:
            age = (datetime.utcnow() - row.evaluated_at).total_seconds()
            if age < TTL_DB:
                result = json.loads(row.result_json)
                # Promote to Tier 1
                with _cache_lock:
                    _mem_cache[symbol] = {"result": result, "ts": time.time()}
                return result
    except Exception as e:
        logger.error(f"Cache DB read error for {symbol}: {e}")
    finally:
        db.close()

    return None


def get_cached_scan() -> Optional[Dict]:
    """Return the full scan results if cached and fresh."""
    with _cache_lock:
        entry = _scan_cache.get("all_results")
        if entry and (time.time() - entry["ts"]) < TTL_SCAN:
            return entry["data"]

    # Try rebuilding from DB (accept results up to 4 hours old)
    db_results = get_all_db_results(max_age_min=240)
    if db_results and len(db_results) > 5:
        scan_data = _build_scan_response(db_results)
        with _cache_lock:
            _scan_cache["all_results"] = {"data": scan_data, "ts": time.time()}
        return scan_data

    return None


def store_result(symbol: str, result: Dict):
    """Store evaluation result in both memory cache and database."""
    symbol = symbol.upper()

    # ── Tier 1: Memory ───────────────────────────────────────────
    with _cache_lock:
        _mem_cache[symbol] = {"result": result, "ts": time.time()}

    # ── Tier 2: Database ─────────────────────────────────────────
    db = SessionLocal()
    try:
        existing = db.query(ScanResult).filter(ScanResult.symbol == symbol).first()
        result_json = json.dumps(result, default=str)

        if existing:
            existing.evaluated_at = datetime.utcnow()
            existing.decision = result.get("decision", "ERROR")
            existing.score = result.get("score", 0)
            existing.probability = result.get("probability", 0)
            existing.ev = result.get("ev", 0)
            existing.entry_price = result.get("entry", 0)
            existing.stop_loss = result.get("stop_loss", 0)
            existing.target_price = result.get("target", 0)
            existing.atr = result.get("atr", 0)
            existing.reward_risk = result.get("reward_risk", 0)
            existing.result_json = result_json
        else:
            db.add(ScanResult(
                symbol=symbol,
                evaluated_at=datetime.utcnow(),
                decision=result.get("decision", "ERROR"),
                score=result.get("score", 0),
                probability=result.get("probability", 0),
                ev=result.get("ev", 0),
                entry_price=result.get("entry", 0),
                stop_loss=result.get("stop_loss", 0),
                target_price=result.get("target", 0),
                atr=result.get("atr", 0),
                reward_risk=result.get("reward_risk", 0),
                result_json=result_json,
            ))

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Cache DB write error for {symbol}: {e}")
    finally:
        db.close()


def store_batch_results(results: List[Dict]):
    """Store multiple results and rebuild the scan cache."""
    for r in results:
        if r and r.get("symbol"):
            store_result(r["symbol"], r)

    # Rebuild scan cache
    scan_data = _build_scan_response(results)
    with _cache_lock:
        _scan_cache["all_results"] = {"data": scan_data, "ts": time.time()}

    logger.info(f"Batch cached: {len(results)} results → memory + DB")


def get_all_db_results(max_age_min: int = 30) -> List[Dict]:
    """Load all evaluation results from DB that aren't too old."""
    cutoff = datetime.utcnow() - timedelta(minutes=max_age_min)
    db = SessionLocal()
    try:
        rows = (
            db.query(ScanResult)
            .filter(ScanResult.evaluated_at >= cutoff)
            .order_by(ScanResult.ev.desc())
            .all()
        )
        results = []
        for row in rows:
            try:
                results.append(json.loads(row.result_json))
            except Exception:
                continue
        return results
    except Exception as e:
        logger.error(f"DB results load error: {e}")
        return []
    finally:
        db.close()


def get_stale_symbols(max_age_min: int = 30) -> List[str]:
    """Return symbols that need re-evaluation (stale or missing)."""
    from app.services.stock_screener import FULL_UNIVERSE

    all_symbols = set(FULL_UNIVERSE.keys())
    cutoff = datetime.utcnow() - timedelta(minutes=max_age_min)

    db = SessionLocal()
    try:
        fresh = {
            row.symbol
            for row in db.query(ScanResult.symbol)
            .filter(ScanResult.evaluated_at >= cutoff)
            .all()
        }
        stale = all_symbols - fresh
        return list(stale)
    except Exception as e:
        logger.error(f"Stale check error: {e}")
        return list(all_symbols)
    finally:
        db.close()


def invalidate(symbol: str = None):
    """Clear memory cache for one symbol or all."""
    with _cache_lock:
        if symbol:
            _mem_cache.pop(symbol.upper(), None)
        else:
            _mem_cache.clear()
            _scan_cache.clear()
    logger.info(f"Eval cache invalidated: {symbol or 'ALL'}")


# ── Helpers ──────────────────────────────────────────────────────────

def _build_scan_response(results: List[Dict]) -> Dict:
    """Build the scan API response from a list of evaluation results."""
    valid = [r for r in results if r and r.get("symbol")]

    accepted = sum(1 for r in valid if r.get("decision") == "ACCEPT")
    rejected = len(valid) - accepted

    # Sort: ACCEPT first (by EV desc), then REJECT
    def sort_key(r):
        priority = {"ACCEPT": 0, "REJECT": 1, "ERROR": 2, "NO_DATA": 3}
        return (priority.get(r.get("decision", "ERROR"), 9), -(r.get("ev", 0) or 0))

    valid.sort(key=sort_key)

    return {
        "results": valid,
        "accepted": accepted,
        "rejected": rejected,
        "total": len(valid),
    }
