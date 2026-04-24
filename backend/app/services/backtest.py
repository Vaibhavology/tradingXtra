"""
TradingXtra Phase 3.5 — Realistic Backtest Engine

Realism features:
  - Entry at next candle open + slippage (0.2%)
  - Risk-based position sizing (1% capital risk per trade)
  - Capital tracking with equity curve
  - Max active trades limit (configurable, default 5)
  - No duplicate symbol positions
  - SL priority on same-bar hits
  - Calibration correction tracking
"""

import logging
from typing import Dict, List, Optional

from app.data_fetcher import get_stock_data, NSE_STOCKS
from app.feature_engine import compute_features, calculate_atr

logger = logging.getLogger(__name__)

# ── Defaults ─────────────────────────────────────────────────────────
DEFAULT_CAPITAL = 100_000.0
RISK_PER_TRADE = 0.01      # 1% of capital risked per trade
SLIPPAGE = 0.002            # 0.2% slippage
MAX_ACTIVE_TRADES = 5
MAX_HOLD_DAYS = 10


def run_backtest(
    symbols: Optional[List[str]] = None,
    lookback_days: int = 60,
    walk_window: int = 30,
    initial_capital: float = DEFAULT_CAPITAL,
    max_active: int = MAX_ACTIVE_TRADES,
) -> Dict:
    """
    Realistic loop-based backtest with capital tracking.

    Args:
        symbols:         Symbols to test (default: all NSE stocks)
        lookback_days:   Total historical days
        walk_window:     Minimum rows for feature computation
        initial_capital: Starting capital (₹)
        max_active:      Max concurrent open positions

    Returns:
        Full results with equity curve, drawdown, per-symbol breakdown
    """
    if symbols is None:
        symbols = [s for s in NSE_STOCKS if s not in ("NIFTY50", "INDIAVIX")]

    market_data = get_stock_data("NIFTY50", days=lookback_days + 30)

    # Load all data upfront
    all_data = {}
    for sym in symbols:
        data = get_stock_data(sym, days=lookback_days + 30)
        if len(data) >= walk_window + 10:
            all_data[sym] = data

    if not all_data:
        return {
            "total_trades": 0, "win_rate": 0, "profit_factor": 0,
            "initial_capital": initial_capital, "final_capital": initial_capital,
            "return_pct": 0, "max_drawdown_pct": 0,
            "equity_curve": [], "per_symbol": {},
        }

    # Run unified simulation across all symbols
    result = _simulate_portfolio(
        all_data, market_data, walk_window,
        initial_capital, max_active,
    )

    return result


def _simulate_portfolio(
    all_data: Dict[str, List[Dict]],
    market_data: List[Dict],
    walk_window: int,
    initial_capital: float,
    max_active: int,
) -> Dict:
    """
    Portfolio-level simulation walking through time.
    Manages capital, position limits, and trade overlap.
    """
    from app.decision_engine import (
        weighted_score, probability_of_win,
        BASE_WEIGHTS, MIN_P_WIN, MIN_EV,
    )

    capital = initial_capital
    equity_curve = [{"step": 0, "capital": round(capital, 2)}]
    active_trades = []   # List of open trade dicts
    closed_trades = []
    symbol_stats = {}

    # Determine the common time range
    min_len = min(len(d) for d in all_data.values())
    n_steps = min_len - 5  # Leave room for forward sim

    # Calibration tracking
    predicted_probs = []
    actual_outcomes = []

    for step in range(walk_window, n_steps):
        # ── 1. Check active trades for exit ──────────────────────
        still_open = []
        for trade in active_trades:
            sym_data = all_data[trade["symbol"]]
            if step >= len(sym_data):
                still_open.append(trade)
                continue

            bar = sym_data[step]
            high, low = bar["high"], bar["low"]
            days_held = step - trade["entry_step"]

            # Update MFE / MAE
            if high - trade["entry_price"] > trade["mfe"]:
                trade["mfe"] = round(high - trade["entry_price"], 2)
            if trade["entry_price"] - low > trade["mae"]:
                trade["mae"] = round(trade["entry_price"] - low, 2)

            # SL check first (conservative)
            if low <= trade["stop_loss"]:
                exit_price = trade["stop_loss"] * (1 - SLIPPAGE)
                pnl_per_share = exit_price - trade["entry_price"]
                pnl = round(pnl_per_share * trade["position_size"], 2)
                capital += pnl

                trade.update({
                    "exit_price": round(exit_price, 2),
                    "exit_step": step,
                    "outcome": "LOSS",
                    "pnl": pnl,
                    "pnl_pct": round(pnl_per_share / trade["entry_price"] * 100, 2),
                    "days_held": days_held,
                })
                closed_trades.append(trade)
                predicted_probs.append(trade["p_win"])
                actual_outcomes.append(0.0)

            elif high >= trade["target"]:
                exit_price = trade["target"] * (1 - SLIPPAGE)
                pnl_per_share = exit_price - trade["entry_price"]
                pnl = round(pnl_per_share * trade["position_size"], 2)
                capital += pnl

                trade.update({
                    "exit_price": round(exit_price, 2),
                    "exit_step": step,
                    "outcome": "WIN",
                    "pnl": pnl,
                    "pnl_pct": round(pnl_per_share / trade["entry_price"] * 100, 2),
                    "days_held": days_held,
                })
                closed_trades.append(trade)
                predicted_probs.append(trade["p_win"])
                actual_outcomes.append(1.0)

            elif days_held >= MAX_HOLD_DAYS:
                # Force close at current close with slippage
                exit_price = bar["close"] * (1 - SLIPPAGE)
                pnl_per_share = exit_price - trade["entry_price"]
                pnl = round(pnl_per_share * trade["position_size"], 2)
                capital += pnl

                outcome = "WIN" if pnl > 0 else "LOSS"
                trade.update({
                    "exit_price": round(exit_price, 2),
                    "exit_step": step,
                    "outcome": outcome,
                    "pnl": pnl,
                    "pnl_pct": round(pnl_per_share / trade["entry_price"] * 100, 2),
                    "days_held": days_held,
                })
                closed_trades.append(trade)
                predicted_probs.append(trade["p_win"])
                actual_outcomes.append(1.0 if pnl > 0 else 0.0)
            else:
                still_open.append(trade)

        active_trades = still_open

        # ── 2. Try to open new trades ────────────────────────────
        if len(active_trades) < max_active and capital > 1000:
            open_symbols = {t["symbol"] for t in active_trades}

            for symbol, sym_data in all_data.items():
                if len(active_trades) >= max_active:
                    break
                if symbol in open_symbols:
                    continue  # No duplicate positions
                if step + 1 >= len(sym_data):
                    continue

                window = sym_data[step - walk_window: step + 1]
                mkt_window = market_data[:step + 1] if market_data else []

                features = compute_features(
                    ohlcv=window,
                    market_ohlcv=mkt_window[-60:] if len(mkt_window) >= 5 else None,
                )

                wscore = weighted_score(features, BASE_WEIGHTS)
                p_win = probability_of_win(wscore)

                closes = [r["close"] for r in window]
                highs = [r["high"] for r in window]
                lows = [r["low"] for r in window]

                atr = calculate_atr(highs, lows, closes, period=14)
                if atr < 0.5:
                    continue

                # Entry at NEXT candle open + slippage
                next_bar = sym_data[step + 1]
                entry_price = next_bar["open"] * (1 + SLIPPAGE)

                sl = entry_price - 1.5 * atr
                target = entry_price + 2.0 * atr
                risk_per_share = entry_price - sl
                reward_per_share = target - entry_price

                if risk_per_share <= 0:
                    continue

                ev = p_win * reward_per_share - (1 - p_win) * risk_per_share

                if p_win < MIN_P_WIN or ev <= MIN_EV:
                    continue

                # Position sizing: risk 1% of capital
                risk_amount = RISK_PER_TRADE * capital
                position_size = max(1, int(risk_amount / risk_per_share))

                # Don't exceed 20% of capital in one trade
                max_shares = int(0.20 * capital / entry_price)
                position_size = min(position_size, max(1, max_shares))

                trade = {
                    "symbol": symbol,
                    "entry_price": round(entry_price, 2),
                    "stop_loss": round(sl, 2),
                    "target": round(target, 2),
                    "entry_step": step + 1,
                    "position_size": position_size,
                    "capital_at_entry": round(capital, 2),
                    "p_win": round(p_win, 4),
                    "wscore": round(wscore, 4),
                    "mfe": 0.0,
                    "mae": 0.0,
                }
                active_trades.append(trade)
                open_symbols.add(symbol)

        # Record equity point
        # Unrealized PnL from open positions
        unrealized = 0.0
        for t in active_trades:
            sym_data = all_data.get(t["symbol"])
            if sym_data and step < len(sym_data):
                curr = sym_data[step]["close"]
                unrealized += (curr - t["entry_price"]) * t["position_size"]

        equity_curve.append({
            "step": step,
            "capital": round(capital + unrealized, 2),
            "open_positions": len(active_trades),
        })

    # ── Force-close remaining trades at last price ───────────────
    for trade in active_trades:
        sym_data = all_data.get(trade["symbol"], [])
        if sym_data:
            exit_price = sym_data[-1]["close"] * (1 - SLIPPAGE)
            pnl_per_share = exit_price - trade["entry_price"]
            pnl = round(pnl_per_share * trade["position_size"], 2)
            capital += pnl
            trade.update({
                "exit_price": round(exit_price, 2),
                "outcome": "WIN" if pnl > 0 else "LOSS",
                "pnl": pnl,
            })
            closed_trades.append(trade)

    # ── Aggregate Results ────────────────────────────────────────
    total = len(closed_trades)
    wins = [t for t in closed_trades if t["outcome"] == "WIN"]
    losses = [t for t in closed_trades if t["outcome"] == "LOSS"]

    gross_profit = sum(t["pnl"] for t in wins) if wins else 0
    gross_loss = abs(sum(t["pnl"] for t in losses)) if losses else 0

    # Per-symbol stats
    for t in closed_trades:
        sym = t["symbol"]
        if sym not in symbol_stats:
            symbol_stats[sym] = {"trades": 0, "wins": 0, "losses": 0, "total_pnl": 0}
        symbol_stats[sym]["trades"] += 1
        if t["outcome"] == "WIN":
            symbol_stats[sym]["wins"] += 1
        else:
            symbol_stats[sym]["losses"] += 1
        symbol_stats[sym]["total_pnl"] = round(symbol_stats[sym]["total_pnl"] + t["pnl"], 2)

    for s in symbol_stats.values():
        s["win_rate"] = round(s["wins"] / s["trades"], 3) if s["trades"] > 0 else 0

    # Max drawdown from equity curve
    max_dd_pct = _compute_curve_drawdown(equity_curve)

    # Calibration analysis
    calibration = _compute_calibration_correction(predicted_probs, actual_outcomes)

    return {
        "total_trades": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / total, 3) if total > 0 else 0,
        "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else 0,
        "initial_capital": initial_capital,
        "final_capital": round(capital, 2),
        "return_pct": round((capital - initial_capital) / initial_capital * 100, 2),
        "total_pnl": round(capital - initial_capital, 2),
        "max_drawdown_pct": round(max_dd_pct, 2),
        "avg_days_held": round(
            sum(t.get("days_held", 0) for t in closed_trades) / total, 1
        ) if total > 0 else 0,
        "slippage_used": SLIPPAGE,
        "risk_per_trade": RISK_PER_TRADE,
        "max_active_trades": max_active,
        "calibration": calibration,
        "equity_curve": equity_curve[::max(1, len(equity_curve) // 50)],  # Sample ~50 points
        "symbols_tested": len(all_data),
        "per_symbol": symbol_stats,
    }


def _compute_curve_drawdown(equity_curve: List[Dict]) -> float:
    """Max drawdown % from equity curve."""
    if len(equity_curve) < 2:
        return 0.0

    peak = equity_curve[0]["capital"]
    max_dd = 0.0

    for point in equity_curve:
        cap = point["capital"]
        if cap > peak:
            peak = cap
        dd_pct = (peak - cap) / peak * 100 if peak > 0 else 0
        if dd_pct > max_dd:
            max_dd = dd_pct

    return max_dd


def _compute_calibration_correction(
    predicted: List[float], actual: List[float]
) -> Dict:
    """
    Compare predicted P(win) vs actual outcomes.
    Returns calibration ratio and suggested correction.
    """
    if len(predicted) < 5:
        return {"samples": len(predicted), "correction": 1.0, "note": "Too few trades"}

    avg_predicted = sum(predicted) / len(predicted)
    avg_actual = sum(actual) / len(actual)

    if avg_predicted > 0:
        ratio = avg_actual / avg_predicted
    else:
        ratio = 1.0

    # Suggested correction multiplier
    if ratio < 0.85:
        correction = 0.95  # Model overestimates → dampen
        note = f"Model overestimates by {(1-ratio)*100:.0f}% — apply 0.95x correction"
    elif ratio > 1.15:
        correction = 1.05  # Model underestimates
        note = f"Model underestimates by {(ratio-1)*100:.0f}% — could be more aggressive"
    else:
        correction = 1.0
        note = "Model well-calibrated"

    return {
        "samples": len(predicted),
        "avg_predicted_pwin": round(avg_predicted, 3),
        "actual_win_rate": round(avg_actual, 3),
        "calibration_ratio": round(ratio, 3),
        "correction": correction,
        "note": note,
    }
