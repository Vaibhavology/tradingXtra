"""
RegimeDetector — Classifies current market regime.

Regimes:
  TRENDING  — Strong directional momentum, calm VIX
  SIDEWAYS  — Range-bound, low momentum
  VOLATILE  — Elevated VIX/ATR, unstable direction

Inputs: NIFTY50 OHLCV (20+ sessions)
"""

import numpy as np
from typing import Dict, List, Optional

from app.feature_engine import calculate_atr, calculate_ema


# Thresholds
EMA_SLOPE_TRENDING = 0.003    # EMA5/EMA20 slope > 0.3% → trending
EMA_SLOPE_SIDEWAYS = 0.001    # EMA slope < 0.1% → sideways
ATR_EXPANSION_RATIO = 1.40    # Current ATR > 1.4× baseline → expansion


def detect(
    market_ohlcv: Optional[List[Dict]] = None,
    vix_ohlcv: Optional[List[Dict]] = None,
) -> Dict:
    """
    Classify market regime from NIFTY50 and VIX data.

    Args:
        market_ohlcv: NIFTY50 OHLCV rows (20+ rows, oldest → newest)
        vix_ohlcv:    India VIX OHLCV rows (optional)

    Returns:
        {regime, confidence, explanation, details}
    """
    if not market_ohlcv or len(market_ohlcv) < 20:
        return {
            "regime": "unknown",
            "confidence": 0.0,
            "explanation": "Insufficient market data for regime detection",
            "details": {},
        }

    closes = [r["close"] for r in market_ohlcv]
    highs = [r["high"] for r in market_ohlcv]
    lows = [r["low"] for r in market_ohlcv]

    # ── EMA Slope ────────────────────────────────────────────────
    ema5 = calculate_ema(closes, 5)
    ema20 = calculate_ema(closes, 20)

    if ema20 > 0:
        ema_slope = (ema5 - ema20) / ema20
    else:
        ema_slope = 0.0

    # ── ATR Expansion ────────────────────────────────────────────
    atr_full = calculate_atr(highs, lows, closes, period=14)
    atr_recent = calculate_atr(highs[-5:], lows[-5:], closes[-5:], period=4)
    atr_ratio = atr_recent / atr_full if atr_full > 0 else 1.0

    # ── VIX Level (if available) ─────────────────────────────────
    vix = None
    if vix_ohlcv and len(vix_ohlcv) >= 1:
        vix = vix_ohlcv[-1].get("close", None)

    vix_volatile = vix is not None and vix >= 20.0
    vix_calm = vix is not None and vix <= 15.0

    # ── Market Return ────────────────────────────────────────────
    ret_5d = (closes[-1] - closes[-6]) / closes[-6] * 100 if len(closes) >= 6 else 0
    ret_10d = (closes[-1] - closes[-11]) / closes[-11] * 100 if len(closes) >= 11 else 0

    details = {
        "ema5": round(ema5, 2),
        "ema20": round(ema20, 2),
        "ema_slope": round(ema_slope, 5),
        "atr_ratio": round(atr_ratio, 3),
        "vix": round(vix, 2) if vix else None,
        "return_5d": round(ret_5d, 2),
        "return_10d": round(ret_10d, 2),
    }

    # ── Classification (priority order) ──────────────────────────

    # Rule 1: Volatile — high VIX OR ATR expanding sharply
    if vix_volatile or atr_ratio > ATR_EXPANSION_RATIO:
        confidence = min(0.95, max(0.55, 0.50 + atr_ratio / 3.0))
        parts = []
        if vix_volatile:
            parts.append(f"VIX elevated at {vix:.1f}")
        if atr_ratio > ATR_EXPANSION_RATIO:
            parts.append(f"ATR expanding ({atr_ratio:.2f}x)")

        return {
            "regime": "volatile",
            "confidence": round(confidence, 4),
            "explanation": f"Volatile market — {', '.join(parts)}",
            "details": details,
        }

    # Rule 2: Trending — strong EMA slope + calm conditions
    if abs(ema_slope) > EMA_SLOPE_TRENDING:
        direction = "up" if ema_slope > 0 else "down"
        confidence = min(0.90, 0.60 + abs(ema_slope) / 0.01)

        return {
            "regime": "trending",
            "confidence": round(confidence, 4),
            "explanation": (
                f"Trending {direction} — EMA5 {'above' if direction == 'up' else 'below'} "
                f"EMA20 by {abs(ema_slope)*100:.2f}%, "
                f"NIFTY {ret_10d:+.1f}% over 10d"
            ),
            "details": {**details, "direction": direction},
        }

    # Rule 3: Sideways — flat EMA, moderate everything
    if abs(ema_slope) < EMA_SLOPE_SIDEWAYS:
        confidence = min(0.85, 0.70 - abs(ema_slope) / EMA_SLOPE_SIDEWAYS * 0.2)

        return {
            "regime": "sideways",
            "confidence": round(confidence, 4),
            "explanation": (
                f"Sideways/range-bound — EMA slope near zero "
                f"({ema_slope*100:.3f}%), {ret_10d:+.1f}% over 10d"
            ),
            "details": details,
        }

    # Default: weakly trending
    direction = "up" if ema_slope > 0 else "down"
    return {
        "regime": "trending",
        "confidence": 0.50,
        "explanation": f"Weakly trending {direction} — EMA slope {ema_slope*100:.3f}%",
        "details": {**details, "direction": direction},
    }
