"""
LiquidityAgent — Assesses trading liquidity from volume and turnover.

Scores based on:
  - Average daily turnover (₹)
  - Volume consistency (coefficient of variation)
  - ATR as a proxy for tradability
"""

import numpy as np
from typing import Dict, List

from app.feature_engine import calculate_atr


def analyze(ohlcv: List[Dict]) -> Dict:
    """
    Assess liquidity from OHLCV data.

    Args:
        ohlcv: OHLCV rows (oldest → newest), minimum 10 rows.

    Returns:
        {liquidity_score, confidence, explanation}
    """
    if len(ohlcv) < 10:
        return {
            "liquidity_score": 0.5,
            "confidence": 0.0,
            "explanation": "Insufficient data for liquidity analysis",
        }

    closes = [r["close"] for r in ohlcv]
    volumes = [r["volume"] for r in ohlcv]
    highs = [r["high"] for r in ohlcv]
    lows = [r["low"] for r in ohlcv]

    avg_vol = float(np.mean(volumes))
    avg_price = float(np.mean(closes[-5:]))
    avg_turnover = avg_vol * avg_price  # ₹ daily

    # Volume consistency — lower CV = more reliable liquidity
    vol_cv = float(np.std(volumes) / (avg_vol + 1e-8))

    # ATR as tradability proxy
    atr = calculate_atr(highs[-15:], lows[-15:], closes[-15:], period=14)
    atr_pct = (atr / closes[-1] * 100) if closes[-1] > 0 else 0

    # ── Turnover-based scoring ───────────────────────────────────
    # ₹5Cr → 0.30, ₹20Cr → 0.70, ₹50Cr+ → 1.0
    if avg_turnover >= 5e8:
        turnover_score = 1.0
    elif avg_turnover >= 2e8:
        turnover_score = 0.70 + 0.30 * (avg_turnover - 2e8) / 3e8
    elif avg_turnover >= 5e7:
        turnover_score = 0.30 + 0.40 * (avg_turnover - 5e7) / 1.5e8
    else:
        turnover_score = max(0.05, avg_turnover / 5e7 * 0.30)

    # ── Penalties ────────────────────────────────────────────────
    # High volume variance = unreliable liquidity
    vol_penalty = 1.0
    if vol_cv > 1.5:
        vol_penalty = 0.85
    elif vol_cv > 2.0:
        vol_penalty = 0.70

    # Very low ATR = stock barely moves = hard to trade
    atr_penalty = 1.0
    if atr_pct < 0.5:
        atr_penalty = 0.80

    score = min(1.0, max(0.0, turnover_score * vol_penalty * atr_penalty))
    confidence = min(0.90, 0.50 + len(ohlcv) / 120.0)

    # ── Explanation ──────────────────────────────────────────────
    turnover_cr = avg_turnover / 1e7  # Convert to crores
    parts = [f"Avg turnover ₹{turnover_cr:.0f}Cr"]

    if vol_cv > 1.5:
        parts.append(f"volume volatile (CV={vol_cv:.1f})")
    if atr_pct < 0.5:
        parts.append(f"very low ATR ({atr_pct:.1f}%)")

    if score >= 0.8:
        quality = "Highly liquid"
    elif score >= 0.5:
        quality = "Adequate liquidity"
    else:
        quality = "Low liquidity"

    explanation = f"{quality} — {', '.join(parts)}"

    return {
        "liquidity_score": round(score, 4),
        "confidence": round(confidence, 4),
        "explanation": explanation,
    }
