"""
TradingXtra Phase 4.5 — Adaptive Portfolio Engine

Upgrades over Phase 4:
  1. Adaptive exposure limits (regime-aware: 70%/50%/40%)
  2. EV-based admission filter (min EV threshold)
  3. Gradual correlation handling (reduce size at 0.7-0.85, hard reject >0.85)
  4. Capital utilization relaxation (lower EV bar when underutilized)
  5. Portfolio-level EV tracking
  6. Risk cluster detection (sector + correlation groups)
  7. Position size cap (20% of capital)
  8. Enhanced portfolio API response
"""

import logging
from typing import Dict, List, Tuple, Optional

import numpy as np

from app.database import SessionLocal, Trade
from app.data_fetcher import get_stock_data, NSE_STOCKS

logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────
DEFAULT_CAPITAL = 100_000.0
RISK_PER_TRADE = 0.01          # 1% of capital per trade
MAX_ACTIVE_TRADES = 5
MAX_SECTOR_EXPOSURE = 0.25     # 25% of capital in one sector
CORRELATION_LOOKBACK = 30      # Days for correlation calculation
SLIPPAGE = 0.002               # 0.2%

# Phase 4.5 adaptive thresholds
CORRELATION_HARD_REJECT = 0.85   # Hard reject above this
CORRELATION_REDUCE_ZONE = 0.70   # Reduce position size 50% in 0.70-0.85 band
EV_THRESHOLD = 0.10             # Minimum EV per share (₹)
EV_RELAXED_THRESHOLD = 0.08     # Relaxed when underutilized
UTILIZATION_LOW_WATERMARK = 0.40 # Below this → relax EV
CLUSTER_SIZE_LIMIT = 3           # Max trades in same sector/cluster
MAX_POSITION_PCT = 0.20         # 20% of capital per position

# Regime-adaptive exposure limits
EXPOSURE_BY_REGIME = {
    "trending":   0.70,  # Strong trend → allow more
    "volatile":   0.40,  # High vol → protect capital
    "mean_revert": 0.50, # Default
    "unknown":    0.50,
}


# ── Regime Helper ────────────────────────────────────────────────────

def _get_current_regime() -> str:
    """Get current market regime from regime_detector."""
    try:
        from app.agents.regime_detector import detect as detect_regime
        market_data = get_stock_data("NIFTY50", days=60)
        vix_data = get_stock_data("INDIAVIX", days=60)
        result = detect_regime(market_data, vix_data)
        return result.get("regime", "unknown")
    except Exception as e:
        logger.warning(f"Regime detection failed: {e}")
        return "unknown"


def get_dynamic_max_exposure(regime: str = None) -> float:
    """Get max exposure based on current regime."""
    if regime is None:
        regime = _get_current_regime()
    return EXPOSURE_BY_REGIME.get(regime, 0.50)


# ── Capital Tracking ─────────────────────────────────────────────────

def get_current_capital() -> float:
    """Compute current capital from trade history."""
    db = SessionLocal()
    try:
        closed = db.query(Trade).filter(Trade.status == "CLOSED").all()
        total_pnl = sum(t.pnl or 0 for t in closed)
        return round(DEFAULT_CAPITAL + total_pnl, 2)
    finally:
        db.close()


def get_open_positions() -> List[Dict]:
    """Get all open positions with current market value."""
    db = SessionLocal()
    try:
        trades = db.query(Trade).filter(Trade.status == "OPEN").all()
        positions = []
        for t in trades:
            current_price = _get_latest_price(t.symbol)
            pos_size = t.position_size or 1
            entry_value = t.entry_price * pos_size
            current_value = current_price * pos_size if current_price > 0 else entry_value
            unrealized_pnl = (current_price - t.entry_price) * pos_size if current_price > 0 else 0

            meta = NSE_STOCKS.get(t.symbol, {})
            positions.append({
                "trade_id": t.id,
                "symbol": t.symbol,
                "name": meta.get("name", t.symbol),
                "sector": meta.get("sector", "Unknown"),
                "entry_price": t.entry_price,
                "current_price": round(current_price, 2),
                "position_size": pos_size,
                "entry_value": round(entry_value, 2),
                "current_value": round(current_value, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "unrealized_pnl_pct": round(unrealized_pnl / entry_value * 100, 2) if entry_value > 0 else 0,
                "stop_loss": t.stop_loss,
                "target": t.target_price,
                "mfe": t.mfe or 0,
                "mae": t.mae or 0,
                "predicted_probability": t.predicted_probability,
                "predicted_ev": t.predicted_ev,
            })
        return positions
    finally:
        db.close()


# ── Portfolio-Level EV ───────────────────────────────────────────────

def compute_portfolio_ev() -> float:
    """Weighted average EV across all open positions."""
    db = SessionLocal()
    try:
        open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
        if not open_trades:
            return 0.0
        total_ev = 0.0
        total_value = 0.0
        for t in open_trades:
            pos_size = t.position_size or 1
            value = t.entry_price * pos_size
            ev = t.predicted_ev or 0
            total_ev += ev * pos_size
            total_value += value
        return round(total_ev / len(open_trades), 2) if open_trades else 0.0
    finally:
        db.close()


# ── Risk Cluster Detection ───────────────────────────────────────────

def detect_risk_clusters() -> Dict:
    """
    Detect concentrated risk clusters by sector.
    Returns cluster info and count.
    """
    positions = get_open_positions()
    sector_counts = {}
    for p in positions:
        sector = p["sector"]
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    clusters = {s: c for s, c in sector_counts.items() if c >= 2}
    return {
        "clusters": clusters,
        "cluster_count": len(clusters),
        "max_cluster_size": max(sector_counts.values()) if sector_counts else 0,
    }


# ── Exposure Calculation ─────────────────────────────────────────────

def compute_exposure(capital: float = None) -> Dict:
    """
    Compute total and per-sector exposure with dynamic limits.
    """
    if capital is None:
        capital = get_current_capital()

    regime = _get_current_regime()
    max_exposure = get_dynamic_max_exposure(regime)
    positions = get_open_positions()

    total_exposure = sum(p["entry_value"] for p in positions)
    total_exposure_pct = (total_exposure / capital * 100) if capital > 0 else 0
    utilization = total_exposure / capital if capital > 0 else 0

    # Sector breakdown
    sectors = {}
    for p in positions:
        sector = p["sector"]
        if sector not in sectors:
            sectors[sector] = {"symbols": [], "exposure": 0.0, "unrealized_pnl": 0.0}
        sectors[sector]["symbols"].append(p["symbol"])
        sectors[sector]["exposure"] += p["entry_value"]
        sectors[sector]["unrealized_pnl"] += p["unrealized_pnl"]

    sector_breakdown = {}
    for sector, data in sectors.items():
        sector_breakdown[sector] = {
            "symbols": data["symbols"],
            "exposure": round(data["exposure"], 2),
            "exposure_pct": round(data["exposure"] / capital * 100, 2) if capital > 0 else 0,
            "unrealized_pnl": round(data["unrealized_pnl"], 2),
        }

    available = capital - total_exposure

    return {
        "capital": round(capital, 2),
        "total_exposure": round(total_exposure, 2),
        "total_exposure_pct": round(total_exposure_pct, 2),
        "capital_utilization": round(utilization, 3),
        "available_capital": round(max(0, available), 2),
        "positions_count": len(positions),
        "max_active_trades": MAX_ACTIVE_TRADES,
        "max_total_exposure_pct": round(max_exposure * 100, 1),
        "max_sector_exposure_pct": MAX_SECTOR_EXPOSURE * 100,
        "regime": regime,
        "sector_breakdown": sector_breakdown,
    }


# ── Correlation ──────────────────────────────────────────────────────

def _compute_returns(ohlcv: List[Dict], days: int = 30) -> List[float]:
    """Compute daily returns from OHLCV data."""
    closes = [r["close"] for r in ohlcv]
    closes = closes[-days:] if len(closes) > days else closes
    if len(closes) < 5:
        return []
    returns = []
    for i in range(1, len(closes)):
        ret = (closes[i] - closes[i - 1]) / closes[i - 1]
        returns.append(ret)
    return returns


def compute_correlation(symbol_a: str, symbol_b: str, days: int = CORRELATION_LOOKBACK) -> float:
    """Pearson correlation between two stocks' daily returns."""
    data_a = get_stock_data(symbol_a, days=days + 10)
    data_b = get_stock_data(symbol_b, days=days + 10)

    ret_a = _compute_returns(data_a, days)
    ret_b = _compute_returns(data_b, days)

    if len(ret_a) < 10 or len(ret_b) < 10:
        return 0.0

    min_len = min(len(ret_a), len(ret_b))
    ret_a = ret_a[-min_len:]
    ret_b = ret_b[-min_len:]

    arr_a = np.array(ret_a)
    arr_b = np.array(ret_b)

    if np.std(arr_a) < 1e-10 or np.std(arr_b) < 1e-10:
        return 0.0

    corr = float(np.corrcoef(arr_a, arr_b)[0, 1])
    return round(corr, 4) if not np.isnan(corr) else 0.0


def check_correlation_with_portfolio(new_symbol: str) -> Tuple[bool, Optional[str], float]:
    """
    Gradual correlation handling:
      - r > 0.85 → hard reject
      - 0.70 < r <= 0.85 → allow but flag for size reduction
      - r <= 0.70 → fully ok

    Returns:
        (ok, reason, size_multiplier) — multiplier < 1.0 means reduce size
    """
    db = SessionLocal()
    try:
        open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()
        open_symbols = [t.symbol for t in open_trades]
    finally:
        db.close()

    if not open_symbols:
        return True, None, 1.0

    worst_corr = 0.0
    worst_pair = ""

    for existing_sym in open_symbols:
        if existing_sym == new_symbol:
            return False, f"Already holding {new_symbol}", 0.0

        corr = compute_correlation(new_symbol, existing_sym)
        if abs(corr) > abs(worst_corr):
            worst_corr = corr
            worst_pair = existing_sym

    if abs(worst_corr) > CORRELATION_HARD_REJECT:
        return False, (
            f"{new_symbol} highly correlated with {worst_pair} "
            f"(r={worst_corr:.2f} > {CORRELATION_HARD_REJECT})"
        ), 0.0

    if abs(worst_corr) > CORRELATION_REDUCE_ZONE:
        return True, (
            f"Moderate correlation with {worst_pair} (r={worst_corr:.2f}) — size reduced 50%"
        ), 0.50

    return True, None, 1.0


# ── EV-Weighted Position Sizing ──────────────────────────────────────

def compute_position_size(
    entry_price: float,
    stop_loss: float,
    ev: float,
    capital: float = None,
    corr_multiplier: float = 1.0,
    cluster_penalty: float = 1.0,
) -> Dict:
    """
    Risk-based position sizing with EV weighting, correlation adjustment,
    and cluster penalty.

    Final size = base * EV_mult * corr_mult * cluster_mult, capped at 20%.
    """
    if capital is None:
        capital = get_current_capital()

    risk_per_share = abs(entry_price - stop_loss)
    if risk_per_share <= 0:
        return {"position_size": 0, "error": "Invalid risk (entry == SL)"}

    # Base size from 1% risk
    risk_amount = RISK_PER_TRADE * capital
    base_size = int(risk_amount / risk_per_share)

    # EV weighting: normalize EV to [0, 0.5] boost
    ev_normalized = max(0, min(0.5, ev / (entry_price * 0.05))) if entry_price > 0 else 0
    ev_multiplier = 1.0 + ev_normalized

    # Apply correlation and cluster adjustments
    sized = int(base_size * ev_multiplier * corr_multiplier * cluster_penalty)

    # Cap: min 1, max 20% of capital
    max_shares = int(MAX_POSITION_PCT * capital / entry_price) if entry_price > 0 else 1
    sized = max(1, min(sized, max_shares))

    return {
        "position_size": sized,
        "risk_amount": round(risk_amount, 2),
        "base_size": base_size,
        "ev_multiplier": round(ev_multiplier, 3),
        "corr_multiplier": round(corr_multiplier, 2),
        "cluster_penalty": round(cluster_penalty, 2),
        "entry_value": round(sized * entry_price, 2),
    }


# ── Trade Admission Control ─────────────────────────────────────────

def admit_trade(decision_result: Dict) -> Tuple[bool, Dict]:
    """
    Full admission control with adaptive intelligence.

    Gates:
      1. Decision = ACCEPT
      2. EV threshold (adaptive based on utilization)
      3. Capital available
      4. Max active trades
      5. Total exposure (regime-adaptive limit)
      6. Sector exposure (25% limit + cluster check)
      7. Correlation (gradual: reduce size at 0.70, reject at 0.85)
    """
    symbol = decision_result.get("symbol", "")
    entry = decision_result.get("entry", 0)
    sl = decision_result.get("stop_loss", 0)
    ev = decision_result.get("ev", 0)
    sector = decision_result.get("sector", "Unknown")

    gates = {}
    admitted = True

    # Gate 1: Decision
    if decision_result.get("decision") != "ACCEPT":
        gates["decision"] = {"pass": False, "reason": "Not ACCEPT"}
        return False, {"admitted": False, "gates": gates}
    gates["decision"] = {"pass": True}

    # Get portfolio state
    capital = get_current_capital()
    regime = _get_current_regime()
    max_exposure = get_dynamic_max_exposure(regime)
    exposure = compute_exposure(capital)
    utilization = exposure.get("capital_utilization", 0)

    # Gate 2: EV threshold (adaptive)
    effective_ev_threshold = EV_THRESHOLD
    if utilization < UTILIZATION_LOW_WATERMARK:
        effective_ev_threshold = EV_RELAXED_THRESHOLD  # Relax when underutilized

    if ev < effective_ev_threshold:
        gates["ev_filter"] = {
            "pass": False,
            "reason": f"EV ₹{ev:.2f} < threshold ₹{effective_ev_threshold:.2f}",
            "utilization": round(utilization, 3),
        }
        admitted = False
    else:
        gates["ev_filter"] = {
            "pass": True,
            "ev": round(ev, 2),
            "threshold": effective_ev_threshold,
            "relaxed": utilization < UTILIZATION_LOW_WATERMARK,
        }

    # Gate 3: Capital available
    if capital < 1000:
        gates["capital"] = {"pass": False, "reason": f"Insufficient capital: ₹{capital:.0f}"}
        admitted = False
    else:
        gates["capital"] = {"pass": True, "capital": round(capital, 2)}

    # Gate 4: Max active trades
    if exposure["positions_count"] >= MAX_ACTIVE_TRADES:
        gates["max_trades"] = {
            "pass": False,
            "reason": f"At limit: {exposure['positions_count']}/{MAX_ACTIVE_TRADES}",
        }
        admitted = False
    else:
        gates["max_trades"] = {
            "pass": True,
            "current": exposure["positions_count"],
            "limit": MAX_ACTIVE_TRADES,
        }

    # Gate 7 (early): Correlation — need multiplier for sizing
    corr_ok, corr_reason, corr_multiplier = check_correlation_with_portfolio(symbol)
    if not corr_ok:
        gates["correlation"] = {"pass": False, "reason": corr_reason}
        admitted = False
    else:
        gates["correlation"] = {
            "pass": True,
            "size_multiplier": corr_multiplier,
            "note": corr_reason,
        }

    # Gate 6 (early): Cluster check — affects sizing
    cluster_info = detect_risk_clusters()
    sector_count = 0
    for p in get_open_positions():
        if p["sector"] == sector:
            sector_count += 1
    cluster_penalty = 1.0
    if sector_count >= CLUSTER_SIZE_LIMIT:
        cluster_penalty = 0.50
        gates["risk_cluster"] = {
            "pass": True,
            "note": f"{sector} cluster ({sector_count} existing) — size halved",
            "penalty": 0.50,
        }
    elif sector_count >= 2:
        cluster_penalty = 0.75
        gates["risk_cluster"] = {
            "pass": True,
            "note": f"{sector} has {sector_count} positions — size reduced 25%",
            "penalty": 0.75,
        }
    else:
        gates["risk_cluster"] = {"pass": True, "penalty": 1.0}

    # Compute position size with all adjustments
    sizing = compute_position_size(
        entry, sl, ev, capital,
        corr_multiplier=corr_multiplier,
        cluster_penalty=cluster_penalty,
    )
    position_value = sizing.get("entry_value", 0)

    # Gate 5: Total exposure (regime-adaptive)
    new_total_exposure = exposure["total_exposure"] + position_value
    new_total_pct = (new_total_exposure / capital * 100) if capital > 0 else 100
    if new_total_pct > max_exposure * 100:
        gates["total_exposure"] = {
            "pass": False,
            "reason": f"Would be {new_total_pct:.1f}% > {max_exposure*100:.0f}% limit (regime={regime})",
        }
        admitted = False
    else:
        gates["total_exposure"] = {
            "pass": True,
            "current_pct": round(exposure["total_exposure_pct"], 1),
            "after_pct": round(new_total_pct, 1),
            "regime_limit": round(max_exposure * 100, 1),
        }

    # Gate 6b: Sector exposure
    sector_exp = exposure["sector_breakdown"].get(sector, {})
    current_sector_exposure = sector_exp.get("exposure", 0)
    new_sector = current_sector_exposure + position_value
    new_sector_pct = (new_sector / capital * 100) if capital > 0 else 100
    if new_sector_pct > MAX_SECTOR_EXPOSURE * 100:
        gates["sector_exposure"] = {
            "pass": False,
            "reason": f"{sector}: would be {new_sector_pct:.1f}% > {MAX_SECTOR_EXPOSURE*100:.0f}% limit",
        }
        admitted = False
    else:
        gates["sector_exposure"] = {
            "pass": True,
            "sector": sector,
            "after_pct": round(new_sector_pct, 1),
        }

    return admitted, {
        "admitted": admitted,
        "symbol": symbol,
        "sector": sector,
        "regime": regime,
        "position_size": sizing.get("position_size", 0),
        "entry_value": position_value,
        "ev_multiplier": sizing.get("ev_multiplier", 1.0),
        "corr_multiplier": corr_multiplier,
        "cluster_penalty": cluster_penalty,
        "capital": round(capital, 2),
        "gates": gates,
    }


# ── Portfolio Metrics ────────────────────────────────────────────────

def get_portfolio_state() -> Dict:
    """
    Complete portfolio state with Phase 4.5 intelligence.
    """
    capital = get_current_capital()
    positions = get_open_positions()
    exposure = compute_exposure(capital)
    regime = exposure.get("regime", "unknown")

    total_unrealized = sum(p["unrealized_pnl"] for p in positions)
    portfolio_ev = compute_portfolio_ev()
    clusters = detect_risk_clusters()

    # Closed trade stats
    db = SessionLocal()
    try:
        closed = db.query(Trade).filter(Trade.status == "CLOSED").all()
        realized_pnl = sum(t.pnl or 0 for t in closed)
        closed_count = len(closed)
    finally:
        db.close()

    max_exp = get_dynamic_max_exposure(regime)

    return {
        "capital": {
            "initial": DEFAULT_CAPITAL,
            "current": round(capital, 2),
            "realized_pnl": round(realized_pnl, 2),
            "unrealized_pnl": round(total_unrealized, 2),
            "total_equity": round(capital + total_unrealized, 2),
        },
        "positions": positions,
        "exposure": exposure,
        "intelligence": {
            "regime": regime,
            "max_exposure_dynamic": round(max_exp * 100, 1),
            "portfolio_EV": portfolio_ev,
            "capital_utilization": exposure.get("capital_utilization", 0),
            "risk_clusters": clusters["cluster_count"],
            "cluster_detail": clusters["clusters"],
        },
        "summary": {
            "open_positions": len(positions),
            "closed_trades": closed_count,
            "total_exposure_pct": exposure["total_exposure_pct"],
            "available_capital_pct": round(
                exposure["available_capital"] / capital * 100, 1
            ) if capital > 0 else 0,
        },
    }


# ── Helper ───────────────────────────────────────────────────────────

def _get_latest_price(symbol: str) -> float:
    """Get latest close price."""
    data = get_stock_data(symbol, days=5)
    return data[-1]["close"] if data else 0.0
