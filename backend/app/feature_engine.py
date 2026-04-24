"""
TradingXtra Phase 1 — Feature Engine

Computes 7 normalized features from OHLCV data.
All outputs bounded [0, 1] via Z-score → sigmoid mapping.

Features:
  PS  PatternStrength     Momentum Z + ATR-normalized move + RSI
  MA  MarketAlignment     Stock direction vs NIFTY50
  SS  SectorStrength      Phase 1: neutral (0.5)
  VC  VolumeConfirmation  Volume Z-score vs rolling baseline
  LS  LiquidityScore      Average daily turnover (piecewise)
  SE  SentimentScore      Phase 1: neutral (0.5)
  MR  ManipulationRisk    Spike dominance + volume abnormality
"""

import math
import logging
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────
MIN_STD_THRESHOLD = 0.005   # Floor to prevent division explosion
ROLLING_WINDOW = 60         # Days for statistical baseline
MIN_DATA_POINTS = 20        # Minimum rows for any calculation


# ── Utility Functions ────────────────────────────────────────────────

def _safe_std(arr: np.ndarray) -> float:
    """Standard deviation with floor to prevent division by near-zero."""
    return max(float(np.std(arr)), MIN_STD_THRESHOLD)


def z_to_unit(z: float) -> float:
    """
    Map Z-score → [0, 1] via sigmoid: 1 / (1 + exp(-z)).
    Clamped to [-6, +6] to prevent math overflow.
    """
    z_clamped = max(-6.0, min(6.0, z))
    return 1.0 / (1.0 + math.exp(-z_clamped))


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi] range."""
    return max(lo, min(hi, value))


# ── Technical Indicators ─────────────────────────────────────────────

def calculate_atr(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14,
) -> float:
    """
    Average True Range — measures volatility.
    TR = max(H-L, |H-prevC|, |L-prevC|)
    ATR = mean(TR over last `period` bars)
    """
    n = min(len(highs), len(lows), len(closes))
    if n < 2:
        return 0.0

    true_ranges = []
    for i in range(1, n):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        true_ranges.append(tr)

    if not true_ranges:
        return 0.0

    return float(np.mean(true_ranges[-period:]))


def calculate_rsi(closes: List[float], period: int = 14) -> float:
    """
    Relative Strength Index.
    Returns value in [0, 100]. Returns 50 (neutral) if insufficient data.
    """
    if len(closes) < period + 1:
        return 50.0

    gains = []
    losses = []
    for i in range(1, len(closes)):
        change = closes[i] - closes[i - 1]
        gains.append(max(0.0, change))
        losses.append(max(0.0, -change))

    avg_gain = float(np.mean(gains[-period:]))
    avg_loss = float(np.mean(losses[-period:]))

    if avg_loss < 1e-10:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def calculate_ema(values: List[float], period: int) -> float:
    """Exponential Moving Average — returns the latest EMA value."""
    if not values:
        return 0.0
    if len(values) <= period:
        return float(np.mean(values))

    multiplier = 2.0 / (period + 1)
    ema = float(np.mean(values[:period]))  # Seed with SMA
    for v in values[period:]:
        ema = (v - ema) * multiplier + ema
    return ema


# ── Main Feature Computation ────────────────────────────────────────

def compute_features(
    ohlcv: List[Dict],
    market_ohlcv: Optional[List[Dict]] = None,
) -> Dict[str, float]:
    """
    Compute 7 normalized features from OHLCV data.

    Args:
        ohlcv:        Stock OHLCV rows (oldest → newest).
                      Each dict: {timestamp, open, high, low, close, volume}
        market_ohlcv: NIFTY50 OHLCV rows (optional, for MarketAlignment).

    Returns:
        Dict with keys PS, MA, SS, VC, LS, SE, MR — all in [0, 1].

    Phase 1 notes:
        SS = 0.5 (no sector index data)
        SE = 0.5 (no sentiment pipeline)
        MR = simplified volume-pattern detection only
    """
    n = len(ohlcv)
    if n < MIN_DATA_POINTS:
        logger.warning(f"Only {n} data points — returning neutral features")
        return {
            "PS": 0.5, "MA": 0.5, "SS": 0.5, "VC": 0.5,
            "LS": 0.5, "SE": 0.5, "MR": 0.15,
        }

    closes = [r["close"] for r in ohlcv]
    highs = [r["high"] for r in ohlcv]
    lows = [r["low"] for r in ohlcv]
    volumes = [r["volume"] for r in ohlcv]

    # ── PS  PatternStrength ──────────────────────────────────────
    # Blend: 50% momentum Z-score, 30% ATR-normalized move, 20% RSI
    lookback = min(10, n - 1)
    move_pct = (closes[-1] - closes[-lookback - 1]) / closes[-lookback - 1] * 100

    # Z-score of 10-day return vs historical distribution
    ten_day_returns = []
    step = min(10, lookback)
    for i in range(step, n):
        ret = (closes[i] - closes[i - step]) / closes[i - step] * 100
        ten_day_returns.append(ret)

    if len(ten_day_returns) >= 5:
        mu = float(np.mean(ten_day_returns))
        sigma = _safe_std(np.array(ten_day_returns))
        move_z = (move_pct - mu) / sigma
    else:
        daily_rets = np.diff(closes) / np.array(closes[:-1]) * 100
        sigma = _safe_std(daily_rets)
        move_z = move_pct / sigma

    # ATR-normalized component
    atr = calculate_atr(highs, lows, closes, period=14)
    if atr > 0:
        price_change_abs = abs(closes[-1] - closes[-lookback - 1])
        move_atr = price_change_abs / atr
        # 1.0 ATR = neutral, 3.0+ = strong
        atr_component = _clamp((move_atr - 1.0) / 2.0, -1.0, 1.0)
        if move_pct < 0:
            atr_component = -atr_component
    else:
        atr_component = 0.0

    # RSI component
    rsi = calculate_rsi(closes, period=14)
    rsi_component = (rsi - 50.0) / 30.0  # RSI=50→0, RSI=80→+1

    ps_raw = 0.50 * move_z + 0.30 * (atr_component * 2.0) + 0.20 * rsi_component
    PS = z_to_unit(ps_raw)

    # ── MA  MarketAlignment ──────────────────────────────────────
    if market_ohlcv and len(market_ohlcv) >= 5:
        mkt_closes = [r["close"] for r in market_ohlcv]
        nifty_chg = (mkt_closes[-1] - mkt_closes[-5]) / mkt_closes[-5] * 100
        direction = 1.0 if move_pct >= 0 else -1.0
        alignment = direction * nifty_chg
        MA = z_to_unit(alignment / 2.0)  # ±2% change ≈ ±1σ
    else:
        MA = 0.5

    # ── SS  SectorStrength ───────────────────────────────────────
    SS = 0.5  # Phase 1: no sector index data

    # ── VC  VolumeConfirmation ───────────────────────────────────
    if n >= 10:
        baseline_vols = np.array(volumes[:-3], dtype=float)
        recent_vols = np.array(volumes[-3:], dtype=float)

        vol_mean = float(np.mean(baseline_vols))
        vol_std = _safe_std(baseline_vols)
        recent_mean = float(np.mean(recent_vols))

        vol_z = (recent_mean - vol_mean) / vol_std
        VC = z_to_unit(vol_z)
    else:
        VC = 0.5

    # ── LS  LiquidityScore ───────────────────────────────────────
    avg_vol = float(np.mean(volumes))
    avg_price = float(np.mean(closes[-5:]))
    avg_turnover = avg_vol * avg_price  # ₹ daily turnover

    # Piecewise: ₹5Cr→0.3, ₹20Cr→0.7, ₹50Cr+→1.0
    if avg_turnover >= 5e8:
        LS = 1.0
    elif avg_turnover >= 2e8:
        LS = 0.7 + 0.3 * (avg_turnover - 2e8) / 3e8
    elif avg_turnover >= 5e7:
        LS = 0.3 + 0.4 * (avg_turnover - 5e7) / 1.5e8
    else:
        LS = max(0.05, avg_turnover / 5e7 * 0.3)

    # ── SE  SentimentScore ───────────────────────────────────────
    SE = 0.5  # Phase 1: no sentiment data

    # ── MR  ManipulationRisk ─────────────────────────────────────
    # Simplified Phase 1: spike dominance + volume abnormality
    if n >= 10:
        # Spike dominance: single day accounts for >60% of total move?
        recent_prices = closes[-10:]
        total_move = abs(recent_prices[-1] - recent_prices[0])
        if total_move > 0:
            daily_moves = [abs(recent_prices[i] - recent_prices[i - 1]) for i in range(1, len(recent_prices))]
            max_daily = max(daily_moves)
            spike_ratio = max_daily / total_move
        else:
            spike_ratio = 0.0

        # Volume abnormality: sudden 1-day spike vs baseline
        vol_ratio = recent_mean / (vol_mean + 1e-8) if n >= 10 else 1.0

        spike_risk = _clamp((spike_ratio - 0.5) / 0.4, 0.0, 1.0)
        vol_risk = _clamp((vol_ratio - 2.5) / 3.0, 0.0, 1.0)

        MR = 0.6 * spike_risk + 0.4 * vol_risk
    else:
        MR = 0.15

    return {
        "PS": round(float(PS), 4),
        "MA": round(float(MA), 4),
        "SS": round(float(SS), 4),
        "VC": round(float(VC), 4),
        "LS": round(float(_clamp(LS)), 4),
        "SE": round(float(SE), 4),
        "MR": round(float(_clamp(MR)), 4),
    }
