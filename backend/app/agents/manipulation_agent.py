"""
ManipulationAgent — Detects potential price manipulation from OHLCV.

Heuristic signals:
  1. Volume spike vs rolling average
  2. Single-day move dominance (one day drives entire move)
  3. Volume-price divergence (volume up but price flat, or vice versa)
"""

import numpy as np
from typing import Dict, List


def analyze(ohlcv: List[Dict]) -> Dict:
    """
    Assess manipulation risk from OHLCV patterns.

    Args:
        ohlcv: OHLCV rows (oldest → newest), minimum 15 rows.

    Returns:
        {manipulation_risk, confidence, signals, explanation}
    """
    if len(ohlcv) < 15:
        return {
            "manipulation_risk": 0.15,
            "confidence": 0.0,
            "signals": {},
            "explanation": "Insufficient data for manipulation analysis",
        }

    closes = [r["close"] for r in ohlcv]
    volumes = [r["volume"] for r in ohlcv]

    signals = {}
    risk_components = []

    # ── Signal 1: Volume Spike ───────────────────────────────────
    # Recent 3-day avg volume vs baseline (older 20+ days)
    baseline_vols = np.array(volumes[:-3], dtype=float)
    recent_vols = np.array(volumes[-3:], dtype=float)

    vol_mean = float(np.mean(baseline_vols))
    recent_mean = float(np.mean(recent_vols))
    vol_ratio = recent_mean / (vol_mean + 1e-8)

    # Ratio > 2.5 = suspicious, > 4.0 = very suspicious
    vol_spike_risk = min(1.0, max(0.0, (vol_ratio - 2.0) / 3.0))
    signals["volume_spike"] = round(vol_ratio, 2)
    risk_components.append(("vol_spike", vol_spike_risk, 0.35))

    # ── Signal 2: Single-Day Move Dominance ──────────────────────
    # If one day's move accounts for >60% of the 10-day total move
    window = min(10, len(closes) - 1)
    recent_closes = closes[-(window + 1):]
    total_move = abs(recent_closes[-1] - recent_closes[0])

    if total_move > 0:
        daily_moves = [abs(recent_closes[i] - recent_closes[i - 1])
                       for i in range(1, len(recent_closes))]
        max_daily = max(daily_moves)
        spike_ratio = max_daily / total_move
    else:
        spike_ratio = 0.0

    spike_risk = min(1.0, max(0.0, (spike_ratio - 0.5) / 0.4))
    signals["spike_dominance"] = round(spike_ratio, 3)
    risk_components.append(("spike_dom", spike_risk, 0.35))

    # ── Signal 3: Volume-Price Divergence ────────────────────────
    # High volume but no price movement = possible accumulation/distribution
    price_change_pct = abs(closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
    vol_change_pct = (recent_mean - vol_mean) / (vol_mean + 1e-8) * 100

    divergence = 0.0
    if vol_change_pct > 50 and price_change_pct < 1.0:
        # High volume, flat price → suspicious
        divergence = min(1.0, vol_change_pct / 200.0)
    signals["vol_price_divergence"] = round(divergence, 3)
    risk_components.append(("divergence", divergence, 0.20))

    # ── Signal 4: Multi-Day Trap (volume spike + next-day drop) ──
    # If volume spiked 2 days ago AND price dropped yesterday → trap
    trap_risk = 0.0
    if len(volumes) >= 5 and len(closes) >= 5:
        vol_2d_ago = volumes[-3]
        vol_baseline = float(np.mean(volumes[:-5])) if len(volumes) > 5 else vol_mean
        price_change_yesterday = (closes[-1] - closes[-2]) / closes[-2] * 100

        if vol_2d_ago > vol_baseline * 2.0 and price_change_yesterday < -0.5:
            trap_risk = min(1.0, (vol_2d_ago / (vol_baseline + 1e-8) - 2.0) / 3.0
                           * abs(price_change_yesterday) / 2.0)
    signals["multi_day_trap"] = round(trap_risk, 3)
    risk_components.append(("trap", trap_risk, 0.15))

    # ── Signal 5: 3-Day Volume Consistency ───────────────────────
    # All 3 recent days elevated vs baseline → sustained abnormality
    consistency_risk = 0.0
    if len(volumes) >= 5:
        days_elevated = sum(1 for v in volumes[-3:] if v > vol_mean * 1.8)
        if days_elevated == 3:
            consistency_risk = min(1.0, (recent_mean / (vol_mean + 1e-8) - 1.5) / 3.0)
    signals["vol_consistency"] = round(consistency_risk, 3)
    risk_components.append(("consistency", consistency_risk, 0.10))

    # ── Composite Risk ───────────────────────────────────────────
    total_risk = sum(risk * weight for _, risk, weight in risk_components)
    total_risk = min(1.0, max(0.0, total_risk))

    # Confidence based on data quality
    confidence = min(0.85, 0.50 + len(ohlcv) / 100.0)

    # ── Explanation ──────────────────────────────────────────────
    warnings = []
    if vol_spike_risk > 0.3:
        warnings.append(f"volume spike {vol_ratio:.1f}x baseline")
    if spike_risk > 0.3:
        warnings.append(f"single-day dominance {spike_ratio:.0%}")
    if divergence > 0.3:
        warnings.append("volume-price divergence")
    if trap_risk > 0.3:
        warnings.append("volume spike followed by price drop (trap signal)")
    if consistency_risk > 0.3:
        warnings.append("sustained 3-day volume abnormality")

    if total_risk >= 0.6:
        level = "HIGH risk"
    elif total_risk >= 0.3:
        level = "Moderate risk"
    else:
        level = "Low risk"

    if warnings:
        explanation = f"{level} — {', '.join(warnings)}"
    else:
        explanation = f"{level} — no suspicious patterns detected"

    return {
        "manipulation_risk": round(total_risk, 4),
        "confidence": round(confidence, 4),
        "signals": signals,
        "explanation": explanation,
    }
