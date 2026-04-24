"""
TradingXtra Phase 2.5 — Decision Engine (Precision Upgrade)

Pipeline:  Data → Agents → News → Regime → Features → Adjusted WScore → P(win) → EV → Accept/Reject

Phase 2.5 upgrades:
  - SE driven by news_service.get_symbol_sentiment() (capped at 0.7)
  - Regime affects risk parameters (SL/target multipliers, P(win) threshold)
  - Market bias integrated into MA scoring
  - VIX/risk alerts boost MR penalty
  - Sideways regime dampens breakout PS
  - Enhanced reasoning with sentiment, bias, and regime context
"""

import math
import logging
from typing import Dict, List, Optional, Tuple

from app.feature_engine import compute_features, calculate_atr
from app.data_fetcher import ensure_data, get_stock_data, NSE_STOCKS

# Agents
from app.agents import pattern_agent, sector_agent, liquidity_agent
from app.agents import manipulation_agent, regime_detector

# News
from app.services.news_service import get_symbol_sentiment

logger = logging.getLogger(__name__)


# ── Scoring Parameters ───────────────────────────────────────────────
BASE_WEIGHTS = {
    "PS": 0.22,   # Pattern Strength
    "MA": 0.18,   # Market Alignment
    "SS": 0.15,   # Sector Strength
    "VC": 0.15,   # Volume Confirmation
    "LS": 0.10,   # Liquidity Score
    "SE": 0.10,   # Sentiment Score
    "MR": 0.10,   # Manipulation Risk (inverted)
}

# Regime-aware weight multipliers (re-normalized after application)
REGIME_ADJUSTMENTS = {
    "trending":  {"PS": 1.15, "MA": 1.15, "MR": 0.90},
    "sideways":  {"PS": 0.80, "MA": 0.85, "SS": 1.20},
    "volatile":  {"PS": 0.75, "MR": 1.30, "LS": 1.10},
}

# Regime-specific risk parameters
REGIME_RISK_PARAMS = {
    "trending":  {"sl_mult": 1.5, "tgt_mult": 2.5, "p_win_boost": -0.02},
    "sideways":  {"sl_mult": 1.5, "tgt_mult": 2.0, "p_win_boost": 0.0},
    "volatile":  {"sl_mult": 1.2, "tgt_mult": 1.8, "p_win_boost": 0.05},
}
DEFAULT_RISK_PARAMS = {"sl_mult": 1.5, "tgt_mult": 2.0, "p_win_boost": 0.0}

K = 10.0
THETA = 0.55

MIN_P_WIN = 0.55
MIN_RR_RATIO = 1.3
MIN_ATR_ABS = 0.5
MIN_EV = 0.0

# Market bias adjustments for MA feature
BIAS_MA_BOOST = {"Bullish": 0.04, "Bearish": -0.04, "Neutral": 0.0}

# VIX threshold for MR penalty
VIX_HIGH_THRESHOLD = 20.0
VIX_MR_PENALTY = 0.08


# ── Core Functions ───────────────────────────────────────────────────

def _get_adjusted_weights(regime: str) -> Dict[str, float]:
    """Apply regime-specific weight multipliers, re-normalize to sum=1."""
    adjustments = REGIME_ADJUSTMENTS.get(regime, {})
    adjusted = {}
    for key, base_w in BASE_WEIGHTS.items():
        adjusted[key] = base_w * adjustments.get(key, 1.0)

    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v / total for k, v in adjusted.items()}
    return adjusted


def weighted_score(features: Dict[str, float], weights: Dict[str, float]) -> float:
    """WScore = Σ (weight_i × feature_i), MR inverted."""
    wscore = (
        weights["PS"] * features["PS"]
        + weights["MA"] * features["MA"]
        + weights["SS"] * features["SS"]
        + weights["VC"] * features["VC"]
        + weights["LS"] * features["LS"]
        + weights["SE"] * features["SE"]
        + weights["MR"] * (1.0 - features["MR"])
    )
    return round(wscore, 4)


def probability_of_win(wscore: float) -> float:
    """P(win) = 1 / (1 + exp(-K × (WScore - θ)))"""
    z = K * (wscore - THETA)
    z_clamped = max(-20.0, min(20.0, z))
    return round(1.0 / (1.0 + math.exp(-z_clamped)), 4)


def compute_risk_reward(closes, highs, lows, sl_mult=1.5, tgt_mult=2.0) -> Dict:
    """ATR-based entry/SL/target with regime-adjustable multipliers."""
    entry = closes[-1]
    atr = calculate_atr(highs, lows, closes, period=14)
    risk_dist = sl_mult * atr
    reward_dist = tgt_mult * atr
    sl = entry - risk_dist
    target = entry + reward_dist
    risk = abs(entry - sl)
    reward = abs(target - entry)
    rr_ratio = reward / risk if risk > 0 else 0.0
    return {
        "entry": round(entry, 2), "stop_loss": round(sl, 2),
        "target": round(target, 2), "atr": round(atr, 2),
        "risk": round(risk, 2), "reward": round(reward, 2),
        "reward_risk": round(rr_ratio, 2),
    }


def calculate_ev(p_win, risk, reward) -> float:
    """EV = P(win) × Reward - (1 - P(win)) × Risk"""
    return round(p_win * reward - (1.0 - p_win) * risk, 2)


def should_reject(p_win, ev, rr_ratio, atr, p_win_threshold=None) -> Tuple[bool, Optional[str]]:
    """Hard rejection rules with adjustable P(win) threshold."""
    min_p = p_win_threshold if p_win_threshold is not None else MIN_P_WIN

    if ev <= MIN_EV:
        return True, f"Negative EV: ₹{ev}"

    if p_win < min_p:
        return True, f"P(win) = {p_win:.2%} < {min_p:.0%} threshold"

    if rr_ratio < MIN_RR_RATIO:
        return True, f"R:R ratio {rr_ratio:.1f} < {MIN_RR_RATIO} minimum"

    if atr < MIN_ATR_ABS:
        return True, f"ATR = ₹{atr:.2f} too low (illiquid or flat)"

    return False, None


# ── Main Entry Point ─────────────────────────────────────────────────

def evaluate(symbol: str, allow_stale: bool = False) -> Dict:
    """
    Full Phase 2.5 evaluation pipeline.

    Steps:
        1. Fetch data (cache → DB → yfinance)
        2. Run agents (pattern, sector, liquidity, manipulation)
        3. Detect regime + get VIX
        4. Get news sentiment (SE)
        5. Compute market bias
        6. Build features (agent-enhanced + context-adjusted)
        7. Regime-adjusted weights → WScore → P(win)
        8. Regime-adjusted risk → SL/target/EV
        9. Rejection rules
        10. Build reasoning + response
    """
    symbol = symbol.upper().strip()
    meta = NSE_STOCKS.get(symbol, {"name": symbol, "sector": "Unknown"})

    logger.info(f"[{symbol}] Starting evaluation...")

    # ── Step 1: Data ─────────────────────────────────────────────
    stock_data = ensure_data(symbol, allow_stale=allow_stale)

    if len(stock_data) < 20:
        logger.warning(f"[{symbol}] Insufficient data: {len(stock_data)} rows")
        return {
            "symbol": symbol, "name": meta.get("name", symbol),
            "sector": meta.get("sector", "Unknown"),
            "score": 0.0, "probability": 0.0, "ev": 0.0,
            "entry": 0.0, "stop_loss": 0.0, "target": 0.0,
            "atr": 0.0, "reward_risk": 0.0,
            "decision": "NO_DATA",
            "rejection_reason": f"Insufficient data: {len(stock_data)} rows",
            "features": {}, "agents": {}, "regime": "unknown",
            "reasoning": [], "data_points": len(stock_data),
        }

    market_data = get_stock_data("NIFTY50", days=120)
    vix_data = get_stock_data("INDIAVIX", days=30)

    # ── Step 2: Run Agents ───────────────────────────────────────
    pattern_result = pattern_agent.analyze(stock_data)
    sector_result = sector_agent.analyze(symbol, stock_data, market_data)
    liquidity_result = liquidity_agent.analyze(stock_data)
    manipulation_result = manipulation_agent.analyze(stock_data)

    # ── Step 3: Regime Detection ─────────────────────────────────
    regime_result = regime_detector.detect(
        market_ohlcv=market_data if len(market_data) >= 20 else None,
        vix_ohlcv=vix_data if vix_data else None,
    )
    regime = regime_result.get("regime", "unknown")

    # ── Step 4: News Sentiment → SE ──────────────────────────────
    try:
        se_raw = get_symbol_sentiment(symbol)
        SE = min(se_raw, 0.7)  # Hard cap — news cannot dominate
    except Exception as e:
        logger.warning(f"[{symbol}] Sentiment fetch failed: {e}")
        SE = 0.5  # Neutral fallback

    # ── Step 4b: Invest Smart boost (YouTube) ─────────────────────
    try:
        from app.services.market_brief import get_invest_smart_stocks
        if symbol in get_invest_smart_stocks():
            SE = min(SE + 0.05, 0.7)  # Light boost only, still capped
    except Exception:
        pass  # Non-critical — silently skip

    # ── Step 5: Market Bias ──────────────────────────────────────
    if len(market_data) >= 6:
        mkt_closes = [r["close"] for r in market_data]
        mkt_ret_5d = (mkt_closes[-1] - mkt_closes[-6]) / mkt_closes[-6] * 100
        if mkt_ret_5d > 1.5:
            market_bias = "Bullish"
        elif mkt_ret_5d < -1.5:
            market_bias = "Bearish"
        else:
            market_bias = "Neutral"
    else:
        mkt_ret_5d = 0.0
        market_bias = "Neutral"

    # VIX level
    vix_level = vix_data[-1]["close"] if vix_data else None

    # ── Step 6: Build Features (agent + context) ─────────────────
    base_features = compute_features(
        ohlcv=stock_data,
        market_ohlcv=market_data if len(market_data) >= 5 else None,
    )

    # Start with agent outputs replacing neutral placeholders
    PS = 0.60 * base_features["PS"] + 0.40 * pattern_result["pattern_score"]
    MA = base_features["MA"]
    SS = sector_result["sector_strength"]
    VC = base_features["VC"]
    LS = liquidity_result["liquidity_score"]
    MR = manipulation_result["manipulation_risk"]

    # ── Context adjustments ──────────────────────────────────────

    # Market bias → MA boost/penalty
    ma_adj = BIAS_MA_BOOST.get(market_bias, 0.0)
    MA = max(0.0, min(1.0, MA + ma_adj))

    # VIX high → increase MR penalty
    if vix_level and vix_level > VIX_HIGH_THRESHOLD:
        MR = min(1.0, MR + VIX_MR_PENALTY)

    # Sideways regime + breakout pattern → dampen PS
    if regime == "sideways" and pattern_result["pattern"] == "breakout":
        PS = max(0.0, PS - 0.08)  # High false breakout risk

    features = {
        "PS": round(PS, 4),
        "MA": round(MA, 4),
        "SS": round(SS, 4),
        "VC": round(VC, 4),
        "LS": round(LS, 4),
        "SE": round(SE, 4),
        "MR": round(MR, 4),
    }

    logger.info(f"[{symbol}] Features: {features} | Regime: {regime} | Bias: {market_bias}")

    # ── Step 7: Regime-Adjusted Score + Probability ──────────────
    weights = _get_adjusted_weights(regime)
    wscore = weighted_score(features, weights)
    p_win = probability_of_win(wscore)

    logger.info(f"[{symbol}] WScore={wscore}, P(win)={p_win}")

    # ── Step 8: Regime-Adjusted Risk / Reward + EV ───────────────
    closes = [r["close"] for r in stock_data]
    highs = [r["high"] for r in stock_data]
    lows = [r["low"] for r in stock_data]

    risk_params = REGIME_RISK_PARAMS.get(regime, DEFAULT_RISK_PARAMS)
    rr = compute_risk_reward(
        closes, highs, lows,
        sl_mult=risk_params["sl_mult"],
        tgt_mult=risk_params["tgt_mult"],
    )
    ev = calculate_ev(p_win, risk=rr["risk"], reward=rr["reward"])

    logger.info(f"[{symbol}] Entry={rr['entry']}, SL={rr['stop_loss']}, "
                f"Tgt={rr['target']}, ATR={rr['atr']}, RR={rr['reward_risk']}, EV={ev}")

    # ── Step 9: Rejection Rules ──────────────────────────────────
    p_win_threshold = MIN_P_WIN + risk_params["p_win_boost"]
    rejected, reason = should_reject(p_win, ev, rr["reward_risk"], rr["atr"], p_win_threshold)
    decision = "REJECT" if rejected else "ACCEPT"

    if rejected:
        logger.info(f"[{symbol}] REJECTED: {reason}")
    else:
        logger.info(f"[{symbol}] ACCEPTED — EV=₹{ev}, P(win)={p_win:.0%}")

    # ── Step 10: Build Reasoning ─────────────────────────────────
    reasoning = []

    # Pattern
    reasoning.append(pattern_result["explanation"])

    # Sector + persistence
    reasoning.append(sector_result["explanation"])

    # Sentiment
    if SE > 0.55:
        reasoning.append(f"Positive news sentiment (SE={SE:.2f})")
    elif SE < 0.45:
        reasoning.append(f"Negative news sentiment (SE={SE:.2f})")
    else:
        reasoning.append("Neutral news sentiment")

    # Market bias
    if market_bias != "Neutral":
        reasoning.append(f"Market bias: {market_bias} (NIFTY {mkt_ret_5d:+.1f}% 5d)")

    # Liquidity
    if liquidity_result["liquidity_score"] < 0.4:
        reasoning.append(f"⚠ {liquidity_result['explanation']}")

    # Manipulation
    if manipulation_result["manipulation_risk"] > 0.3:
        reasoning.append(f"⚠ {manipulation_result['explanation']}")
    elif manipulation_result["manipulation_risk"] < 0.1:
        reasoning.append("Clean price action — no manipulation signals")

    # VIX context
    if vix_level and vix_level > VIX_HIGH_THRESHOLD:
        reasoning.append(f"⚠ India VIX elevated at {vix_level:.1f} — increased risk")

    # Regime
    reasoning.append(f"Regime: {regime_result['explanation']}")

    # ── Response ─────────────────────────────────────────────────
    agents_summary = {
        "pattern": {
            "score": pattern_result["pattern_score"],
            "type": pattern_result["pattern"],
            "confidence": pattern_result["confidence"],
        },
        "sector": {
            "score": sector_result["sector_strength"],
            "sector": sector_result["sector"],
            "confidence": sector_result["confidence"],
        },
        "liquidity": {
            "score": liquidity_result["liquidity_score"],
            "confidence": liquidity_result["confidence"],
        },
        "manipulation": {
            "risk": manipulation_result["manipulation_risk"],
            "confidence": manipulation_result["confidence"],
        },
        "regime": {
            "regime": regime,
            "confidence": regime_result["confidence"],
        },
        "sentiment": {
            "score": SE,
            "source": "news_rss",
        },
    }

    return {
        "symbol": symbol,
        "name": meta.get("name", symbol),
        "sector": meta.get("sector", "Unknown"),
        "score": wscore,
        "probability": p_win,
        "ev": ev,
        "entry": rr["entry"],
        "stop_loss": rr["stop_loss"],
        "target": rr["target"],
        "atr": rr["atr"],
        "reward_risk": rr["reward_risk"],
        "decision": decision,
        "rejection_reason": reason,
        "features": features,
        "agents": agents_summary,
        "regime": regime,
        "market_bias": market_bias,
        "reasoning": reasoning,
        "data_points": len(stock_data),
    }
