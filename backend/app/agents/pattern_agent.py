"""
PatternAgent — Detects chart patterns from OHLCV data.

Patterns detected:
  breakout      — Close above N-day rolling high
  consolidation — Low ATR + tight range (pre-breakout)
  trend         — Sustained directional move
  pullback      — Retracement within a trend
"""

import numpy as np
from typing import Dict, List

from app.feature_engine import calculate_atr


def analyze(ohlcv: List[Dict]) -> Dict:
    """
    Analyze recent price action for chart patterns.

    Args:
        ohlcv: OHLCV rows (oldest → newest), minimum 20 rows.

    Returns:
        {pattern_score, pattern, confidence, explanation}
    """
    if len(ohlcv) < 20:
        return {
            "pattern_score": 0.5,
            "pattern": "insufficient_data",
            "confidence": 0.0,
            "explanation": f"Need 20+ rows, got {len(ohlcv)}",
        }

    closes = [r["close"] for r in ohlcv]
    highs = [r["high"] for r in ohlcv]
    lows = [r["low"] for r in ohlcv]

    current = closes[-1]
    lookback = min(20, len(closes) - 1)

    # ── Breakout Detection ───────────────────────────────────────
    # Close > highest close of the previous N days (excluding today)
    prev_high = max(closes[-lookback - 1:-1])
    prev_low = min(closes[-lookback - 1:-1])
    is_breakout = current > prev_high
    breakout_pct = (current - prev_high) / prev_high * 100 if prev_high > 0 else 0

    # ── Consolidation Detection ──────────────────────────────────
    atr = calculate_atr(highs[-15:], lows[-15:], closes[-15:], period=14)
    atr_pct = (atr / current * 100) if current > 0 else 0
    range_20 = ((max(highs[-lookback:]) - min(lows[-lookback:])) / current * 100)
    is_consolidating = atr_pct < 2.0 and range_20 < 8.0

    # ── Trend Strength ───────────────────────────────────────────
    ret_10d = (closes[-1] - closes[-11]) / closes[-11] * 100 if len(closes) >= 11 else 0
    ret_5d = (closes[-1] - closes[-6]) / closes[-6] * 100 if len(closes) >= 6 else 0

    # ── Classification ───────────────────────────────────────────
    if is_breakout:
        score = min(1.0, 0.65 + breakout_pct / 8.0)
        confidence = min(0.95, 0.70 + breakout_pct / 15.0)
        pattern = "breakout"
        explanation = (
            f"Breakout above {lookback}-day high "
            f"(₹{prev_high:.0f} → ₹{current:.0f}, +{breakout_pct:.1f}%)"
        )

    elif is_consolidating:
        score = 0.40
        confidence = 0.65
        pattern = "consolidation"
        explanation = (
            f"Tight consolidation — ATR={atr_pct:.1f}%, "
            f"{lookback}d range={range_20:.1f}% (potential breakout setup)"
        )

    elif ret_10d > 3.0 and ret_5d > 0:
        # Uptrend — strong recent momentum
        score = min(1.0, 0.55 + ret_10d / 20.0)
        confidence = min(0.85, 0.55 + abs(ret_10d) / 25.0)
        pattern = "trend"
        explanation = f"Uptrend — +{ret_10d:.1f}% over 10d, +{ret_5d:.1f}% over 5d"

    elif ret_10d < -3.0:
        # Downtrend / weakness
        score = max(0.0, 0.40 + ret_10d / 20.0)
        confidence = min(0.80, 0.50 + abs(ret_10d) / 25.0)
        pattern = "pullback"
        explanation = f"Pullback — {ret_10d:.1f}% over 10d"

    else:
        # Neutral — no clear pattern
        score = 0.50
        confidence = 0.40
        pattern = "neutral"
        explanation = f"No clear pattern (10d: {ret_10d:+.1f}%, range: {range_20:.1f}%)"

    return {
        "pattern_score": round(score, 4),
        "pattern": pattern,
        "confidence": round(confidence, 4),
        "explanation": explanation,
    }
