"""
TradingXtra Phase 3.5 — Trade Monitor Service

Realism features:
  - Slippage on exits (0.2%)
  - Position sizing (1% capital risk per trade)
  - Capital-aware trade creation
  - Max active trades limit (5)
  - MFE/MAE tracking
"""

import logging
from datetime import datetime
from typing import List, Dict

from app.database import SessionLocal, Trade
from app.data_fetcher import get_stock_data

logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────
SLIPPAGE = 0.002             # 0.2%
RISK_PER_TRADE = 0.01        # 1% of capital
MAX_ACTIVE_TRADES = 5
DEFAULT_CAPITAL = 100_000.0


def _get_latest_price(symbol: str) -> float:
    """Get latest close price for a symbol."""
    data = get_stock_data(symbol, days=5)
    if data:
        return data[-1]["close"]
    return 0.0


def _get_current_capital() -> float:
    """
    Compute current capital from trade history.
    Start with DEFAULT_CAPITAL, add/subtract all closed PnL.
    """
    db = SessionLocal()
    try:
        closed = db.query(Trade).filter(Trade.status == "CLOSED").all()
        total_pnl = sum(t.pnl or 0 for t in closed)
        return DEFAULT_CAPITAL + total_pnl
    finally:
        db.close()


def check_open_trades() -> Dict:
    """
    Check all OPEN trades against current prices.

    For each open trade:
      - Update MFE/MAE
      - If price >= target → WIN (exit with slippage)
      - If price <= stop_loss → LOSS (exit with slippage)
      - PnL scaled by position_size

    Returns summary of what was processed.
    """
    db = SessionLocal()
    try:
        open_trades = db.query(Trade).filter(Trade.status == "OPEN").all()

        if not open_trades:
            logger.info("Trade monitor: no open trades")
            return {"checked": 0, "closed": 0, "wins": 0, "losses": 0}

        closed = 0
        wins = 0
        losses = 0

        for trade in open_trades:
            price = _get_latest_price(trade.symbol)
            if price <= 0:
                continue

            pos_size = trade.position_size or 1

            # Update MFE (max price seen since entry)
            excursion_up = price - trade.entry_price
            if excursion_up > (trade.mfe or 0):
                trade.mfe = round(excursion_up, 2)

            # Update MAE (max drawdown since entry)
            excursion_down = trade.entry_price - price
            if excursion_down > (trade.mae or 0):
                trade.mae = round(excursion_down, 2)

            # Check target hit
            if price >= trade.target_price:
                exit_price = round(price * (1 - SLIPPAGE), 2)
                pnl_per_share = exit_price - trade.entry_price
                trade.status = "CLOSED"
                trade.exit_price = exit_price
                trade.exit_timestamp = datetime.utcnow()
                trade.outcome = "WIN"
                trade.pnl = round(pnl_per_share * pos_size, 2)
                trade.pnl_pct = round(pnl_per_share / trade.entry_price * 100, 2)
                trade.actual_result = 1.0
                closed += 1
                wins += 1
                logger.info(
                    f"Trade {trade.symbol} → WIN "
                    f"(entry ₹{trade.entry_price} → exit ₹{exit_price}, "
                    f"{pos_size} shares, PnL ₹{trade.pnl})"
                )

            # Check stop-loss hit
            elif price <= trade.stop_loss:
                exit_price = round(price * (1 - SLIPPAGE), 2)
                pnl_per_share = exit_price - trade.entry_price
                trade.status = "CLOSED"
                trade.exit_price = exit_price
                trade.exit_timestamp = datetime.utcnow()
                trade.outcome = "LOSS"
                trade.pnl = round(pnl_per_share * pos_size, 2)
                trade.pnl_pct = round(pnl_per_share / trade.entry_price * 100, 2)
                trade.actual_result = 0.0
                closed += 1
                losses += 1
                logger.info(
                    f"Trade {trade.symbol} → LOSS "
                    f"(entry ₹{trade.entry_price} → exit ₹{exit_price}, "
                    f"{pos_size} shares, PnL ₹{trade.pnl})"
                )

        db.commit()

        summary = {
            "checked": len(open_trades),
            "closed": closed,
            "wins": wins,
            "losses": losses,
            "still_open": len(open_trades) - closed,
        }
        logger.info(f"Trade monitor: {summary}")
        return summary

    except Exception as e:
        db.rollback()
        logger.error(f"Trade monitor error: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        db.close()


def create_trade(decision_result: Dict) -> Dict:
    """
    Record a trade from a decision engine result.

    Phase 4: Routes through portfolio admission control.
    All gates must pass: capital, exposure, sector, correlation.
    """
    if decision_result.get("decision") != "ACCEPT":
        return {"recorded": False, "reason": "Not ACCEPT"}

    # Run through portfolio admission gates
    from app.services.portfolio import admit_trade

    admitted, admission = admit_trade(decision_result)

    if not admitted:
        # Find first failed gate for the reason
        failed_gates = [
            f"{k}: {v.get('reason', 'failed')}"
            for k, v in admission.get("gates", {}).items()
            if not v.get("pass", True)
        ]
        reason = "; ".join(failed_gates) if failed_gates else "Portfolio admission rejected"
        logger.info(f"Trade {decision_result['symbol']} blocked: {reason}")
        return {"recorded": False, "reason": reason, "gates": admission.get("gates", {})}

    # All gates passed — create the trade
    db = SessionLocal()
    try:
        position_size = admission.get("position_size", 1)
        capital = admission.get("capital", DEFAULT_CAPITAL)

        trade = Trade(
            symbol=decision_result["symbol"],
            entry_price=decision_result["entry"],
            stop_loss=decision_result["stop_loss"],
            target_price=decision_result["target"],
            decision="ACCEPT",
            timestamp=datetime.utcnow(),
            status="OPEN",
            predicted_probability=decision_result.get("probability"),
            predicted_ev=decision_result.get("ev"),
            regime_at_entry=decision_result.get("regime"),
            score_at_entry=decision_result.get("score"),
            position_size=position_size,
            capital_at_entry=round(capital, 2),
            slippage_applied=SLIPPAGE,
        )

        db.add(trade)
        db.commit()
        db.refresh(trade)

        logger.info(
            f"Trade recorded: {trade.symbol} "
            f"entry=₹{trade.entry_price} SL=₹{trade.stop_loss} "
            f"tgt=₹{trade.target_price} size={position_size} shares "
            f"EV_mult={admission.get('ev_multiplier', 1.0):.2f} "
            f"P(win)={trade.predicted_probability:.2%}"
        )

        return {
            "recorded": True,
            "trade_id": trade.id,
            "symbol": trade.symbol,
            "entry": trade.entry_price,
            "stop_loss": trade.stop_loss,
            "target": trade.target_price,
            "position_size": position_size,
            "ev_multiplier": admission.get("ev_multiplier", 1.0),
            "capital": round(capital, 2),
            "gates": admission.get("gates", {}),
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Trade creation error: {e}", exc_info=True)
        return {"recorded": False, "error": str(e)}
    finally:
        db.close()


def get_open_trades() -> List[Dict]:
    """Get all currently open trades."""
    db = SessionLocal()
    try:
        trades = db.query(Trade).filter(Trade.status == "OPEN").all()
        return [
            {
                "id": t.id, "symbol": t.symbol,
                "entry_price": t.entry_price, "stop_loss": t.stop_loss,
                "target_price": t.target_price, "timestamp": t.timestamp.isoformat(),
                "position_size": t.position_size,
                "mfe": t.mfe, "mae": t.mae,
                "predicted_probability": t.predicted_probability,
                "regime_at_entry": t.regime_at_entry,
            }
            for t in trades
        ]
    finally:
        db.close()


def get_all_trades(limit: int = 100) -> List[Dict]:
    """Get recent trades (all statuses)."""
    db = SessionLocal()
    try:
        trades = (
            db.query(Trade)
            .order_by(Trade.timestamp.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": t.id, "symbol": t.symbol,
                "entry_price": t.entry_price, "stop_loss": t.stop_loss,
                "target_price": t.target_price, "decision": t.decision,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "status": t.status, "exit_price": t.exit_price,
                "exit_timestamp": t.exit_timestamp.isoformat() if t.exit_timestamp else None,
                "outcome": t.outcome, "pnl": t.pnl, "pnl_pct": t.pnl_pct,
                "position_size": t.position_size,
                "capital_at_entry": t.capital_at_entry,
                "mfe": t.mfe, "mae": t.mae,
                "predicted_probability": t.predicted_probability,
                "predicted_ev": t.predicted_ev,
                "actual_result": t.actual_result,
                "regime_at_entry": t.regime_at_entry,
                "score_at_entry": t.score_at_entry,
            }
            for t in trades
        ]
    finally:
        db.close()
