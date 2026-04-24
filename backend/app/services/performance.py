"""
TradingXtra Phase 3.5 — Performance Metrics

Computes aggregate performance stats from closed trades.
Includes equity curve, capital tracking, and calibration.
"""

import logging
from typing import Dict, List

from app.database import SessionLocal, Trade

logger = logging.getLogger(__name__)


def compute_metrics() -> Dict:
    """
    Compute aggregate performance metrics from all closed trades.

    Returns:
        {total_trades, open_trades, closed_trades, win_rate,
         avg_win, avg_loss, profit_factor, total_pnl,
         max_drawdown, calibration}
    """
    db = SessionLocal()
    try:
        all_trades = db.query(Trade).all()
        closed = [t for t in all_trades if t.status == "CLOSED"]
        open_trades = [t for t in all_trades if t.status == "OPEN"]

        initial_capital = 100_000.0  # Matches trade_monitor default

        if not closed:
            return {
                "total_trades": len(all_trades),
                "open_trades": len(open_trades),
                "closed_trades": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "total_pnl": 0.0,
                "initial_capital": initial_capital,
                "current_capital": initial_capital,
                "return_pct": 0.0,
                "max_drawdown": 0.0,
                "max_drawdown_pct": 0.0,
                "best_trade": None,
                "worst_trade": None,
                "calibration": {},
                "equity_curve": [],
            }

        wins = [t for t in closed if t.outcome == "WIN"]
        losses = [t for t in closed if t.outcome == "LOSS"]

        win_pnls = [t.pnl for t in wins if t.pnl is not None]
        loss_pnls = [t.pnl for t in losses if t.pnl is not None]

        # Win rate
        win_rate = len(wins) / len(closed) if closed else 0.0

        # Average win/loss
        avg_win = sum(win_pnls) / len(win_pnls) if win_pnls else 0.0
        avg_loss = sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0.0

        # Profit factor = gross profits / gross losses
        gross_profit = sum(win_pnls) if win_pnls else 0.0
        gross_loss = abs(sum(loss_pnls)) if loss_pnls else 0.0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        # Total PnL
        all_pnls = [t.pnl for t in closed if t.pnl is not None]
        total_pnl = sum(all_pnls)

        # Max drawdown (sequential PnL curve)
        max_dd = _compute_max_drawdown(closed)

        # Best/worst trades
        best = max(closed, key=lambda t: t.pnl or 0)
        worst = min(closed, key=lambda t: t.pnl or 0)

        best_trade = {
            "symbol": best.symbol, "pnl": best.pnl,
            "pnl_pct": best.pnl_pct, "entry": best.entry_price,
        }
        worst_trade = {
            "symbol": worst.symbol, "pnl": worst.pnl,
            "pnl_pct": worst.pnl_pct, "entry": worst.entry_price,
        }

        # Calibration: P(win) vs actual outcomes
        calibration = _compute_calibration(closed)

        # MFE/MAE analysis
        avg_mfe = sum(t.mfe or 0 for t in closed) / len(closed)
        avg_mae = sum(t.mae or 0 for t in closed) / len(closed)

        # Equity curve from closed trades
        equity_curve = _build_equity_curve(closed, initial_capital)
        current_capital = initial_capital + total_pnl
        return_pct = (current_capital - initial_capital) / initial_capital * 100

        # Max drawdown %
        max_dd_pct = 0.0
        if equity_curve:
            peak = equity_curve[0]["capital"]
            for pt in equity_curve:
                if pt["capital"] > peak:
                    peak = pt["capital"]
                dd = (peak - pt["capital"]) / peak * 100 if peak > 0 else 0
                if dd > max_dd_pct:
                    max_dd_pct = dd

        return {
            "total_trades": len(all_trades),
            "open_trades": len(open_trades),
            "closed_trades": len(closed),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(win_rate, 4),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "total_pnl": round(total_pnl, 2),
            "initial_capital": initial_capital,
            "current_capital": round(current_capital, 2),
            "return_pct": round(return_pct, 2),
            "max_drawdown": round(max_dd, 2),
            "max_drawdown_pct": round(max_dd_pct, 2),
            "avg_mfe": round(avg_mfe, 2),
            "avg_mae": round(avg_mae, 2),
            "best_trade": best_trade,
            "worst_trade": worst_trade,
            "calibration": calibration,
            "equity_curve": equity_curve,
        }

    finally:
        db.close()


def _compute_max_drawdown(closed_trades: List) -> float:
    """
    Max drawdown from sequential PnL curve.
    Trades sorted by exit timestamp.
    """
    sorted_trades = sorted(
        closed_trades,
        key=lambda t: t.exit_timestamp or t.timestamp,
    )

    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0

    for t in sorted_trades:
        pnl = t.pnl or 0
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        dd = peak - cumulative
        if dd > max_dd:
            max_dd = dd

    return max_dd


def _build_equity_curve(closed_trades: List, initial_capital: float) -> List[Dict]:
    """Build equity curve from closed trades."""
    sorted_trades = sorted(
        closed_trades,
        key=lambda t: t.exit_timestamp or t.timestamp,
    )

    curve = [{"timestamp": None, "capital": round(initial_capital, 2), "trade_num": 0}]
    capital = initial_capital

    for i, t in enumerate(sorted_trades, 1):
        capital += t.pnl or 0
        ts = t.exit_timestamp or t.timestamp
        curve.append({
            "timestamp": ts.isoformat() if ts else None,
            "capital": round(capital, 2),
            "trade_num": i,
            "symbol": t.symbol,
            "outcome": t.outcome,
        })

    return curve


def _compute_calibration(closed_trades: List) -> Dict:
    """
    Compare predicted P(win) with actual outcomes.

    Buckets predictions into ranges and computes actual win rate per bucket.
    Useful for model calibration assessment.
    """
    buckets = {
        "0.50-0.60": {"predicted_avg": 0, "actual_wins": 0, "count": 0},
        "0.60-0.70": {"predicted_avg": 0, "actual_wins": 0, "count": 0},
        "0.70-0.80": {"predicted_avg": 0, "actual_wins": 0, "count": 0},
        "0.80-0.90": {"predicted_avg": 0, "actual_wins": 0, "count": 0},
        "0.90-1.00": {"predicted_avg": 0, "actual_wins": 0, "count": 0},
    }

    for t in closed_trades:
        p = t.predicted_probability
        if p is None:
            continue

        if p < 0.60:
            bucket = "0.50-0.60"
        elif p < 0.70:
            bucket = "0.60-0.70"
        elif p < 0.80:
            bucket = "0.70-0.80"
        elif p < 0.90:
            bucket = "0.80-0.90"
        else:
            bucket = "0.90-1.00"

        buckets[bucket]["count"] += 1
        buckets[bucket]["predicted_avg"] += p
        if t.outcome == "WIN":
            buckets[bucket]["actual_wins"] += 1

    # Compute averages
    result = {}
    for key, data in buckets.items():
        if data["count"] > 0:
            result[key] = {
                "trades": data["count"],
                "predicted_avg": round(data["predicted_avg"] / data["count"], 3),
                "actual_win_rate": round(data["actual_wins"] / data["count"], 3),
            }

    return result


def compute_by_regime() -> Dict:
    """Performance breakdown by market regime at entry."""
    db = SessionLocal()
    try:
        closed = db.query(Trade).filter(Trade.status == "CLOSED").all()
        if not closed:
            return {}

        regimes = {}
        for t in closed:
            r = t.regime_at_entry or "unknown"
            if r not in regimes:
                regimes[r] = {"wins": 0, "losses": 0, "total_pnl": 0.0}
            if t.outcome == "WIN":
                regimes[r]["wins"] += 1
            else:
                regimes[r]["losses"] += 1
            regimes[r]["total_pnl"] += t.pnl or 0

        for r, data in regimes.items():
            total = data["wins"] + data["losses"]
            data["trades"] = total
            data["win_rate"] = round(data["wins"] / total, 3) if total > 0 else 0
            data["total_pnl"] = round(data["total_pnl"], 2)

        return regimes
    finally:
        db.close()
