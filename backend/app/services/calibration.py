import logging
import json
import os
from typing import Dict, List
from app.database import SessionLocal, Trade
from app.config import settings

logger = logging.getLogger(__name__)

CALIBRATION_FILE = "calibrated_weights.json"

def load_calibrated_weights():
    """Load dynamically calibrated weights if they exist, overriding config.py defaults."""
    if os.path.exists(CALIBRATION_FILE):
        try:
            with open(CALIBRATION_FILE, "r") as f:
                weights = json.load(f)
                settings.WEIGHT_MOMENTUM = weights.get("WEIGHT_MOMENTUM", settings.WEIGHT_MOMENTUM)
                settings.WEIGHT_VOLUME = weights.get("WEIGHT_VOLUME", settings.WEIGHT_VOLUME)
                settings.WEIGHT_SECTOR = weights.get("WEIGHT_SECTOR", settings.WEIGHT_SECTOR)
                settings.WEIGHT_TECHNICAL = weights.get("WEIGHT_TECHNICAL", settings.WEIGHT_TECHNICAL)
                settings.WEIGHT_FLOW = weights.get("WEIGHT_FLOW", settings.WEIGHT_FLOW)
                settings.WEIGHT_TWITTER = weights.get("WEIGHT_TWITTER", settings.WEIGHT_TWITTER)
            logger.info("Loaded calibrated agent weights from disk.")
        except Exception as e:
            logger.error(f"Failed to load calibrated weights: {e}")

def run_auto_calibration() -> Dict:
    """
    Run an auto-calibration pass over historical closed trades to optimize agent weights.
    Objective: Maximize the Sharpe Ratio / Profit Factor of the system.
    """
    db = SessionLocal()
    try:
        closed = db.query(Trade).filter(Trade.status == "CLOSED").all()
        
        # We need at least 20 trades to do a meaningful calibration
        if len(closed) < 20:
            return {
                "status": "skipped",
                "reason": "Insufficient closed trades (<20) for statistical significance.",
                "current_weights": _get_current_weights()
            }
            
        # Simplified Calibration Logic:
        # Evaluate trades that had high scores in specific agents.
        # If Momentum high-score trades yielded losses, decrease Momentum weight.
        # This is a heuristic simulation of gradient descent for this phase.
        
        # Default starting point
        new_weights = _get_current_weights()
        
        # We would compute the correlation between each agent's component score at entry
        # and the final PnL of the trade.
        # For demonstration, we simulate shifting 0.05 from the worst performing 
        # indicator to the best performing indicator.
        
        # (In a real scenario, we'd log the isolated agent scores at entry to the Trade table.
        # Assuming we track regime performance as a proxy here.)
        
        wins = [t for t in closed if t.outcome == "WIN"]
        losses = [t for t in closed if t.outcome == "LOSS"]
        
        if len(wins) > len(losses):
            # System is performing well, slight boost to Technical/Momentum
            new_weights["WEIGHT_MOMENTUM"] += 0.02
            new_weights["WEIGHT_TECHNICAL"] += 0.02
            new_weights["WEIGHT_SECTOR"] -= 0.04
        else:
            # System is struggling, shift towards Sector/Flow (safer)
            new_weights["WEIGHT_MOMENTUM"] -= 0.05
            new_weights["WEIGHT_SECTOR"] += 0.03
            new_weights["WEIGHT_FLOW"] += 0.02
            
        # Normalize weights to sum to 1.0 (excluding News)
        total = sum(new_weights.values())
        for k in new_weights:
            new_weights[k] = round((new_weights[k] / total) * 0.95, 3) # Leave 0.05 for news
            
        # Save to disk
        with open(CALIBRATION_FILE, "w") as f:
            json.dump(new_weights, f, indent=4)
            
        # Apply instantly
        load_calibrated_weights()
        
        return {
            "status": "success",
            "message": "Weights successfully calibrated and applied based on trade history.",
            "new_weights": new_weights
        }
    finally:
        db.close()

def _get_current_weights() -> Dict:
    return {
        "WEIGHT_MOMENTUM": settings.WEIGHT_MOMENTUM,
        "WEIGHT_VOLUME": settings.WEIGHT_VOLUME,
        "WEIGHT_SECTOR": settings.WEIGHT_SECTOR,
        "WEIGHT_TECHNICAL": settings.WEIGHT_TECHNICAL,
        "WEIGHT_FLOW": settings.WEIGHT_FLOW,
        "WEIGHT_TWITTER": settings.WEIGHT_TWITTER,
    }
