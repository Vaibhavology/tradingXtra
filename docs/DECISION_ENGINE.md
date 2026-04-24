# Final Decision Engine Architecture

## Overview

The Final Decision Engine is the SINGLE SOURCE OF TRUTH for all trading decisions. It aggregates outputs from multiple advisory agents, applies hard risk rules, and produces the final Top 10 picks that the frontend displays.

## Decision Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    FINAL DECISION ENGINE                        │
│                    (AUTHORITATIVE)                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  1. Aggregate all agent outputs                          │   │
│  │  2. Apply hard risk rules (NON-NEGOTIABLE)               │   │
│  │  3. Resolve conflicts (disagreement = risk signal)       │   │
│  │  4. Cross-platform verification check                    │   │
│  │  5. Approve / Reject stocks                              │   │
│  │  6. Produce FINAL Top 10 only                            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   Technical   │   │  Fundamental  │   │  News/Budget  │
│    Agent      │   │    Agent      │   │    Agent      │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│   FII/DII     │   │   Sentiment   │   │ Chart Vision  │
│    Agent      │   │    Agent      │   │    Agent      │
└───────────────┘   └───────────────┘   └───────────────┘
                              │
                              ▼
                    ┌───────────────┐
                    │Cross-Platform │
                    │ Verification  │
                    │    Agent      │
                    └───────────────┘
```

## Advisory Agents (Non-Authoritative)

Each agent provides EVIDENCE ONLY. They do not make final decisions.

### 1. Technical Agent
- Price action analysis
- Chart patterns
- Support/Resistance levels
- Volume analysis
- Moving averages
- RSI, MACD, other indicators

### 2. Fundamental Agent
- PAT (Profit After Tax)
- ROCE (Return on Capital Employed)
- Debt levels
- Earnings quality
- Order book analysis
- Quarterly results

### 3. News & Budget Agent
- Budget announcements
- Policy changes
- Macro events
- Sector-specific news
- Regulatory changes

### 4. FII/DII Flow Agent
- Foreign Institutional Investor flows
- Domestic Institutional Investor flows
- Block deals
- Bulk deals
- Delivery percentage

### 5. Social Sentiment Agent
- Social media sentiment
- Retail sentiment indicators
- News sentiment
- Forum discussions

### 6. Chart Pattern / Vision Agent
- AI-based pattern recognition
- Candlestick patterns
- Chart formations
- Trend analysis

### 7. Cross-Platform Verification Agent
- Compares signals across platforms
- Detects contradictions
- Flags manipulation
- Identifies pump-and-dump patterns
- Checks governance issues

## Hard Rules (CANNOT BE OVERRIDDEN)

These rules are absolute. No agent output can override them.

### Rule 1: Market Regime Conflict → REJECT
```python
if setup.direction != market_regime.direction:
    if market_regime.strength > 70:
        return REJECT("Market regime conflict")
```

### Rule 2: SL Risk Beyond Limits → REJECT
```python
risk_percent = abs(entry - stop_loss) / entry * 100
if risk_percent > user_settings.max_risk_per_trade:
    return REJECT("SL risk exceeds limits")
```

### Rule 3: Agent Disagreement → REJECT
```python
disagreeing_agents = count_strong_disagreements(agent_outputs)
if disagreeing_agents >= 2:
    return REJECT("Major agent disagreement")
```

### Rule 4: Manipulation/Governance Flag → REJECT or DOWNGRADE
```python
if cross_check.status == "CRITICAL":
    return REJECT("Manipulation flag detected")
if cross_check.status == "WARNING":
    confidence = confidence * 0.8  # Downgrade
    add_warning_to_output(cross_check.issues)
```

### Rule 5: Social Hype Cannot Override
```python
if sentiment_agent.score > 90 and fundamental_agent.score < 50:
    return REJECT("Social hype without fundamental support")
```

### Rule 6: Pattern Confidence Cannot Override SL
```python
if pattern.confidence > 90 and risk_reward < 1.5:
    return REJECT("Pattern confidence cannot override poor R:R")
```

## Conflict Resolution

When agents disagree, the system treats it as a RISK SIGNAL, not something to average away.

```python
def resolve_conflicts(agent_outputs):
    # Count agreements and disagreements
    bullish_count = sum(1 for a in agent_outputs if a.direction == "LONG")
    bearish_count = sum(1 for a in agent_outputs if a.direction == "SHORT")
    
    # Strong disagreement = risk
    if bullish_count >= 2 and bearish_count >= 2:
        return {
            "action": "REJECT",
            "reason": "Strong agent disagreement - treat as risk"
        }
    
    # Weak disagreement = downgrade confidence
    if bullish_count >= 1 and bearish_count >= 1:
        return {
            "action": "DOWNGRADE",
            "confidence_multiplier": 0.85
        }
    
    return {"action": "PROCEED"}
```

## Cross-Platform Verification Logic

```python
def cross_platform_check(symbol, signals):
    issues = []
    
    # Check for unusual volume without news
    if signals.volume_spike and not signals.has_news:
        issues.append("Unusual volume spike without news")
    
    # Check for conflicting analyst sentiment
    if signals.analyst_bullish_count > 0 and signals.analyst_bearish_count > 0:
        if abs(signals.analyst_bullish_count - signals.analyst_bearish_count) < 2:
            issues.append("Conflicting analyst sentiment")
    
    # Check for governance flags
    if signals.governance_flag:
        issues.append("Negative governance flag on alternate platform")
    
    # Check for pump-and-dump patterns
    if signals.social_spike > 200 and signals.price_spike > 5:
        issues.append("Potential pump-and-dump pattern detected")
    
    # Determine status
    if any("governance" in i.lower() or "pump" in i.lower() for i in issues):
        status = "CRITICAL"
    elif len(issues) > 0:
        status = "WARNING"
    else:
        status = "OK"
    
    return {
        "status": status,
        "issues": issues,
        "platformsChecked": 4
    }
```

## Final Output Structure

The Decision Engine produces ONLY the final approved picks:

```json
{
  "picks": [
    {
      "id": "1",
      "symbol": "RELIANCE",
      "name": "Reliance Industries",
      "direction": "LONG",
      "entryZone": { "low": 2420, "high": 2445 },
      "stopLoss": 2385,
      "target1": 2510,
      "target2": 2580,
      "expectedMove": 3.8,
      "confidence": 82,
      "pattern": { ... },
      "reasoning": [ ... ],
      "crossCheck": { "status": "OK", "issues": [], "platformsChecked": 4 },
      "riskReward": 2.1,
      "sector": "Energy",
      "_internal": {
        "agentScores": { ... },
        "rulesApplied": [ ... ],
        "conflictsResolved": [ ... ]
      }
    }
  ],
  "rejected": [
    {
      "symbol": "XYZ",
      "reason": "Market regime conflict",
      "rule": "RULE_1"
    }
  ],
  "metadata": {
    "totalCandidates": 50,
    "approved": 10,
    "rejected": 40,
    "timestamp": "2024-01-15T09:15:00Z"
  }
}
```

Note: `_internal` and `rejected` are NOT sent to frontend. Frontend sees ONLY final approved picks.

## Key Principles

1. **Backend is the single source of truth**
2. **Frontend never decides trades**
3. **AI outputs are constrained by rules**
4. **Disagreements are risk signals, not averaged away**
5. **Explainability over prediction**
6. **Risk discipline always wins**
