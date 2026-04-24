"""
Technical Indicators Utility
Helper functions for technical analysis
"""

from typing import List, Tuple

def calculate_sma(prices: List[float], period: int) -> float:
    """Calculate Simple Moving Average"""
    if len(prices) < period:
        return sum(prices) / len(prices) if prices else 0
    return sum(prices[-period:]) / period

def calculate_ema(prices: List[float], period: int) -> float:
    """Calculate Exponential Moving Average"""
    if len(prices) < period:
        return calculate_sma(prices, len(prices))
    
    multiplier = 2 / (period + 1)
    ema = calculate_sma(prices[:period], period)
    
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate Relative Strength Index"""
    if len(prices) < period + 1:
        return 50  # Neutral if insufficient data
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)

def find_support_resistance(prices: List[float], lookback: int = 20) -> Tuple[List[float], List[float]]:
    """Find support and resistance levels from price history"""
    if len(prices) < lookback:
        lookback = len(prices)
    
    recent = prices[-lookback:]
    
    # Simple approach: use recent highs/lows
    supports = [min(recent), min(recent) * 0.98]
    resistances = [max(recent), max(recent) * 1.02]
    
    return supports, resistances

def calculate_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    """Calculate Average True Range"""
    if len(highs) < period or len(lows) < period or len(closes) < period:
        return 0
    
    true_ranges = []
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        )
        true_ranges.append(tr)
    
    return sum(true_ranges[-period:]) / period if true_ranges else 0

def detect_trend(prices: List[float]) -> str:
    """Detect trend direction"""
    if len(prices) < 5:
        return "neutral"
    
    sma_short = calculate_sma(prices, 5)
    sma_long = calculate_sma(prices, min(20, len(prices)))
    
    if sma_short > sma_long * 1.01:
        return "bullish"
    elif sma_short < sma_long * 0.99:
        return "bearish"
    else:
        return "neutral"
