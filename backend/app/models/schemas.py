"""Pydantic schemas for API request/response models"""

from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

# ============ Market Status ============

class MarketStatusResponse(BaseModel):
    nifty: str
    nifty_value: float
    bank_nifty: str
    bank_nifty_value: float
    vix: float
    vix_change: float
    top_sector: str
    fii_flow: str
    dii_flow: str
    market_open: bool
    timestamp: str

# ============ Stock Pick ============

class StockPick(BaseModel):
    symbol: str
    name: str
    sector: str
    direction: str  # LONG or SHORT
    momentum_score: float
    volume_multiple: float
    sector_strength: float
    entry: List[float]  # [low, high]
    sl: float
    targets: List[float]  # [target1, target2]
    expected_move: float
    confidence: float
    reasons: List[str]
    twitter_status: str  # trending / not_trending / negative
    warnings: List[str]

class TodayPicksResponse(BaseModel):
    date: str
    market_regime: str
    picks: List[StockPick]
    total_candidates: int
    passed_momentum_gate: int
    passed_volume_gate: int
    passed_sector_gate: int
    final_count: int

# ============ Twitter ============

class TwitterSignal(BaseModel):
    symbol: str
    mentions: int
    engagement_score: float
    theme: str
    sentiment: float
    is_confirmed: bool  # True only if price+volume also confirm

class TwitterSignalsResponse(BaseModel):
    signals: List[TwitterSignal]
    timestamp: str
    note: str  # Always remind: Twitter is supporting only

# ============ Debug Output ============

class StockEvaluation(BaseModel):
    symbol: str
    name: str
    sector: str
    
    # Raw values
    price_move_pct: float
    volume_multiple: float
    sector_vs_nifty: float
    delivery_pct: float
    
    # Gate results
    passed_momentum_gate: bool
    passed_volume_gate: bool
    passed_sector_gate: bool
    passed_manipulation_check: bool
    
    # Scores
    momentum_score: float
    volume_score: float
    sector_score: float
    flow_score: float
    twitter_score: float
    final_score: float
    
    # Decision
    included: bool
    rejection_reason: Optional[str]

class DebugOutput(BaseModel):
    timestamp: str
    all_evaluations: List[StockEvaluation]
    rejected: List[Dict]
    selected: List[str]
