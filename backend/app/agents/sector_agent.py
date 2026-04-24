"""
SectorAgent — Measures stock's relative strength vs market.

Uses NIFTY50 as the market proxy. Computes how much the stock
is outperforming or underperforming the broader index.
"""

import math
from typing import Dict, List, Optional

from app.data_fetcher import NSE_STOCKS


def _compute_return(ohlcv: List[Dict], period: int = 10) -> float:
    """N-day % return from OHLCV data."""
    if len(ohlcv) < period + 1:
        return 0.0
    closes = [r["close"] for r in ohlcv]
    old = closes[-(period + 1)]
    new = closes[-1]
    return ((new - old) / old * 100) if old > 0 else 0.0


def _sigmoid(x: float) -> float:
    """Map value to [0,1] via sigmoid."""
    x = max(-6.0, min(6.0, x))
    return 1.0 / (1.0 + math.exp(-x))


def analyze(
    symbol: str,
    stock_ohlcv: List[Dict],
    market_ohlcv: Optional[List[Dict]] = None,
) -> Dict:
    """
    Compute sector-relative strength.

    Args:
        symbol:       Stock symbol (e.g., "RELIANCE")
        stock_ohlcv:  Stock OHLCV rows
        market_ohlcv: NIFTY50 OHLCV rows (optional)

    Returns:
        {sector_strength, sector, confidence, explanation}
    """
    meta = NSE_STOCKS.get(symbol.upper(), {})
    sector = meta.get("sector", "Unknown")

    if len(stock_ohlcv) < 11:
        return {
            "sector_strength": 0.5,
            "sector": sector,
            "confidence": 0.0,
            "explanation": "Insufficient data for sector analysis",
        }

    stock_ret_10 = _compute_return(stock_ohlcv, 10)
    stock_ret_5 = _compute_return(stock_ohlcv, 5)
    stock_ret_3 = _compute_return(stock_ohlcv, 3)

    # ── Trend Persistence Check ──────────────────────────────────
    # Multi-day consistency: are 3d, 5d, 10d all in same direction?
    directions = [stock_ret_3 > 0, stock_ret_5 > 0, stock_ret_10 > 0]
    trend_consistent = all(directions) or not any(directions)

    # Single-day spike detection: if >60% of 5d return in 1 day → unreliable
    spike_detected = False
    if len(stock_ohlcv) >= 6:
        closes = [r["close"] for r in stock_ohlcv]
        total_5d_move = abs(closes[-1] - closes[-6])
        if total_5d_move > 0:
            daily_moves = [abs(closes[-(i+1)] - closes[-(i+2)]) for i in range(5)]
            max_single = max(daily_moves)
            spike_detected = (max_single / total_5d_move) > 0.60

    if market_ohlcv and len(market_ohlcv) >= 11:
        market_ret_10 = _compute_return(market_ohlcv, 10)
        market_ret_5 = _compute_return(market_ohlcv, 5)

        # Relative strength: how much stock outperforms market
        relative_10 = stock_ret_10 - market_ret_10
        relative_5 = stock_ret_5 - market_ret_5

        # Blended relative: 60% 10-day, 40% 5-day
        relative = 0.6 * relative_10 + 0.4 * relative_5

        # Score: 5% outperformance → ~0.73 via sigmoid
        score = _sigmoid(relative / 4.0)

        # Confidence: base + adjustments for consistency
        confidence = min(0.85, 0.60 + abs(relative) / 20.0)
        if trend_consistent:
            confidence = min(0.90, confidence + 0.08)
        if spike_detected:
            confidence = max(0.25, confidence - 0.15)

        # Trend persistence boost/penalty to score
        if trend_consistent and abs(relative) > 1.0:
            # Multi-day trend confirmed → slight score boost
            score = min(1.0, score + 0.03)

        if relative > 2.0:
            explanation = (
                f"{sector} — outperforming NIFTY by {relative:.1f}pp "
                f"(stock {stock_ret_10:+.1f}% vs NIFTY {market_ret_10:+.1f}%)"
            )
        elif relative < -2.0:
            explanation = (
                f"{sector} — underperforming NIFTY by {abs(relative):.1f}pp "
                f"(stock {stock_ret_10:+.1f}% vs NIFTY {market_ret_10:+.1f}%)"
            )
        else:
            explanation = (
                f"{sector} — in-line with market "
                f"(stock {stock_ret_10:+.1f}% vs NIFTY {market_ret_10:+.1f}%)"
            )

        if trend_consistent:
            explanation += " [multi-day trend confirmed]"
        if spike_detected:
            explanation += " [single-day spike — lower confidence]"
    else:
        # No market data — use absolute return as proxy
        score = _sigmoid(stock_ret_10 / 5.0)
        confidence = 0.40
        if spike_detected:
            confidence = max(0.20, confidence - 0.10)
        explanation = f"{sector} — stock return {stock_ret_10:+.1f}% (no market comparison)"

    return {
        "sector_strength": round(score, 4),
        "sector": sector,
        "confidence": round(confidence, 4),
        "explanation": explanation,
    }
