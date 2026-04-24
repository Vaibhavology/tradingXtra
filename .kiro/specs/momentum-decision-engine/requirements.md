# Requirements Document

## Introduction

This document specifies the requirements for a Momentum-Oriented Final Decision Engine for Indian equity trading. The system prioritizes active momentum, strong volume, and sector support over traditional "clean chart" patterns. It incorporates Twitter sentiment as a discovery/confirmation layer while maintaining strict momentum and volume gates.

## Glossary

- **Decision_Engine**: The authoritative system component that produces final Top 10 stock picks after applying all filters, gates, and ranking criteria
- **Momentum_Gate**: The initial filter that rejects stocks failing minimum momentum and volume thresholds
- **Sector_Strength**: A measure of how a sector is performing relative to NIFTY 50
- **Volume_Expansion**: Volume compared to 20-day average, expressed as a multiplier (e.g., 1.5×)
- **Twitter_Scout**: The agent that monitors Twitter for trader attention and momentum themes
- **Relative_Performance**: A stock's performance compared to its sector or NIFTY benchmark
- **Delivery_Percentage**: The percentage of traded volume that results in actual delivery (indicates conviction)
- **Swing_Trade**: A trade held for 1-10 sessions targeting 3-8% moves

## Requirements

### Requirement 1: Momentum Gate Filter

**User Story:** As a momentum trader, I want stocks that fail minimum momentum criteria to be automatically rejected, so that I only see stocks with active price movement.

#### Acceptance Criteria

1. WHEN a stock has less than 4% price move in the last 5-10 sessions AND volume is less than 1.5× the 20-day average, THEN the Decision_Engine SHALL reject the stock from consideration
2. WHEN a stock passes the momentum gate, THEN the Decision_Engine SHALL include it in the candidate pool for ranking
3. WHEN calculating the 5-10 session move, THE Decision_Engine SHALL use the maximum move within that window (not just endpoint)
4. IF a stock has exactly 4% move OR exactly 1.5× volume, THEN the Decision_Engine SHALL include it (boundary is inclusive)

### Requirement 2: Sector-Relative Performance Analysis

**User Story:** As a trader, I want stocks underperforming their sector to be downgraded, so that I focus on sector leaders rather than laggards.

#### Acceptance Criteria

1. WHEN a stock is underperforming its sector index over the last 5 sessions, THEN the Decision_Engine SHALL apply a confidence downgrade of 10-15%
2. WHEN a stock is underperforming NIFTY 50 over the last 5 sessions, THEN the Decision_Engine SHALL apply an additional confidence downgrade of 5-10%
3. WHEN a stock is outperforming both its sector AND NIFTY, THEN the Decision_Engine SHALL apply a confidence boost of up to 10%
4. THE Decision_Engine SHALL calculate relative performance as (stock_return - benchmark_return) over the comparison period

### Requirement 3: Sector Representation in Final Output

**User Story:** As a diversified momentum trader, I want the Top 10 to include stocks from outperforming sectors, so that I capture broad market momentum themes.

#### Acceptance Criteria

1. THE Decision_Engine SHALL include at least 3 stocks from sectors currently outperforming NIFTY in the final Top 10
2. WHEN fewer than 3 qualifying stocks exist from outperforming sectors, THEN the Decision_Engine SHALL include all available and note the shortfall
3. THE Decision_Engine SHALL identify outperforming sectors as those with 5-session returns exceeding NIFTY by at least 0.5%
4. WHEN multiple stocks from the same outperforming sector qualify, THE Decision_Engine SHALL limit to maximum 3 per sector to maintain diversification

### Requirement 4: Weighted Ranking System

**User Story:** As a momentum trader, I want stocks ranked by a weighted scoring system that prioritizes momentum and volume, so that the Top 10 reflects true momentum leaders.

#### Acceptance Criteria

1. THE Decision_Engine SHALL calculate final scores using these weights:
   - Recent momentum (5-10 session move): 25%
   - Volume expansion (vs 20-day avg): 20%
   - Sector strength (sector vs NIFTY): 15%
   - Technical structure (pattern quality): 15%
   - Flow/delivery (FII/DII + delivery %): 15%
   - News/social sentiment: 10%
2. WHEN two stocks have equal final scores, THE Decision_Engine SHALL rank the stock with higher volume expansion first
3. THE Decision_Engine SHALL normalize each factor to a 0-100 scale before applying weights
4. THE Decision_Engine SHALL output the final weighted score as the confidence value (0-100)

### Requirement 5: Twitter Momentum Scout Integration

**User Story:** As a trader, I want Twitter sentiment to boost confidence for stocks that already pass momentum filters, so that I can identify stocks with active trader attention.

#### Acceptance Criteria

1. WHEN a stock is trending on Twitter AND passes price momentum AND volume filters, THEN the Decision_Engine SHALL increase confidence by 5-10%
2. WHEN a stock trends on Twitter but lacks price/volume confirmation, THEN the Decision_Engine SHALL treat it as hype and NOT include it in the Top 10
3. THE Twitter_Scout SHALL never override momentum, volume, sector strength, or risk rules
4. WHEN Twitter sentiment is negative for a stock that passes all other filters, THEN the Decision_Engine SHALL add a warning flag but NOT reject the stock
5. THE Decision_Engine SHALL log Twitter as a "discovery" or "confirmation" source, never as "decision authority"

### Requirement 6: Volume-Based Momentum Validation

**User Story:** As a trader, I want high-volume trend continuation to be recognized as valid momentum rather than manipulation, so that I don't miss legitimate breakouts.

#### Acceptance Criteria

1. WHEN a stock shows high volume (>2× 20-day avg) WITH price trend continuation in the same direction, THEN the Decision_Engine SHALL classify it as "valid momentum"
2. WHEN a stock shows high volume WITH price reversal or no follow-through, THEN the Decision_Engine SHALL flag it as "potential distribution" and downgrade confidence by 15%
3. WHEN delivery percentage exceeds 50% on high-volume days, THEN the Decision_Engine SHALL boost confidence by 5% (indicates genuine buying)
4. IF volume spike occurs without corresponding price move (>2% in direction), THEN the Decision_Engine SHALL flag as "suspicious activity"

### Requirement 7: Final Output Format

**User Story:** As a swing trader, I want the final Top 10 output to include all information needed for trade execution, so that I can act quickly on momentum opportunities.

#### Acceptance Criteria

1. THE Decision_Engine SHALL output exactly 10 stocks (or fewer if insufficient candidates pass gates)
2. FOR EACH stock in the Top 10, THE Decision_Engine SHALL provide:
   - Symbol and name
   - Direction (LONG/SHORT)
   - Entry zone (price range)
   - Stop-loss level
   - Target 1 and Target 2
   - Final confidence score (0-100)
   - Momentum score breakdown
   - Volume expansion multiplier
   - Sector and sector strength
   - Twitter status (trending/not trending/negative)
3. THE Decision_Engine SHALL sort the Top 10 by final confidence score in descending order
4. WHEN a stock has warnings (Twitter negative, suspicious volume, etc.), THE Decision_Engine SHALL include them in a warnings array

### Requirement 8: Hard Rejection Rules

**User Story:** As a risk-conscious trader, I want certain conditions to automatically reject stocks regardless of other scores, so that I avoid high-risk situations.

#### Acceptance Criteria

1. IF a stock fails the momentum gate (Requirement 1), THEN the Decision_Engine SHALL reject it regardless of other factors
2. IF a stock has a governance or manipulation flag from cross-platform verification, THEN the Decision_Engine SHALL reject it
3. IF stop-loss risk exceeds user's configured maximum risk per trade, THEN the Decision_Engine SHALL reject it
4. IF a stock is trending on Twitter but has ZERO price/volume confirmation, THEN the Decision_Engine SHALL reject it as pure hype
5. THE Decision_Engine SHALL log all rejections with reason codes for audit purposes

### Requirement 9: Scoring Normalization

**User Story:** As a system operator, I want all scoring factors normalized consistently, so that the weighted ranking produces meaningful comparisons.

#### Acceptance Criteria

1. THE Decision_Engine SHALL normalize momentum score: 0 = 0% move, 100 = 10%+ move (linear scale)
2. THE Decision_Engine SHALL normalize volume score: 0 = 1× avg, 100 = 3×+ avg (linear scale, capped)
3. THE Decision_Engine SHALL normalize sector strength: 0 = -2% vs NIFTY, 100 = +2% vs NIFTY (linear scale)
4. THE Decision_Engine SHALL normalize technical score based on pattern confidence from vision agent (0-100 passthrough)
5. THE Decision_Engine SHALL normalize flow score: combination of FII/DII direction and delivery % (0-100)
6. THE Decision_Engine SHALL normalize sentiment score: -100 to +100 Twitter sentiment mapped to 0-100

### Requirement 10: Audit Trail

**User Story:** As a trader reviewing past decisions, I want a complete audit trail of how each stock was scored and ranked, so that I can understand and improve the system.

#### Acceptance Criteria

1. FOR EACH stock evaluated, THE Decision_Engine SHALL log:
   - Raw values for all 6 scoring factors
   - Normalized scores for each factor
   - Weighted contribution of each factor
   - Any adjustments (sector underperformance, Twitter boost, etc.)
   - Final decision (included/rejected) with reason
2. THE Decision_Engine SHALL timestamp all evaluations
3. THE Decision_Engine SHALL make audit data available via internal API (not exposed to frontend)
4. WHEN a stock is rejected, THE Decision_Engine SHALL log which gate or rule caused rejection
