# Design Document: Momentum-Oriented Decision Engine

## Overview

This design specifies a momentum-first trading decision engine that prioritizes active price movement, volume expansion, and sector strength over traditional pattern-based analysis. The system implements a multi-stage pipeline: gate filtering → scoring → ranking → output generation, with Twitter sentiment as a non-authoritative confirmation layer.

The engine is designed for Indian equity markets (NSE/BSE) targeting swing trades of 1-10 sessions with 3-8% expected moves.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Price Data    │  Volume Data   │  Sector Data   │  Twitter Data  │  Flows │
│  (5-20 days)   │  (20-day avg)  │  (vs NIFTY)    │  (Scout API)   │ FII/DII│
└───────┬────────┴───────┬────────┴───────┬────────┴───────┬────────┴────┬───┘
        │                │                │                │             │
        ▼                ▼                ▼                ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MOMENTUM GATE (Stage 1)                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  REJECT IF: (move_5_10_sessions < 4%) AND (volume < 1.5× 20d_avg)   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│              ┌───────────────┴───────────────┐                              │
│              ▼                               ▼                              │
│         REJECTED                        CANDIDATES                          │
│         (logged)                        (to Stage 2)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SCORING ENGINE (Stage 2)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Momentum    │  │   Volume     │  │   Sector     │  │  Technical   │    │
│  │  Scorer      │  │   Scorer     │  │   Scorer     │  │   Scorer     │    │
│  │   (25%)      │  │    (20%)     │  │    (15%)     │  │    (15%)     │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│  ┌──────────────┐  ┌──────────────┐                                        │
│  │    Flow      │  │  Sentiment   │                                        │
│  │   Scorer     │  │   Scorer     │                                        │
│  │    (15%)     │  │    (10%)     │                                        │
│  └──────────────┘  └──────────────┘                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ADJUSTMENT LAYER (Stage 3)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  • Sector underperformance penalty (-10% to -25%)                          │
│  • Twitter confirmation boost (+5% to +10%)                                 │
│  • Volume validation adjustment (±15%)                                      │
│  • Diversification constraints (max 3 per sector)                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      FINAL RANKING (Stage 4)                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Sort by adjusted confidence score (descending)                         │
│  2. Ensure ≥3 stocks from outperforming sectors                            │
│  3. Apply hard rejection rules                                              │
│  4. Select Top 10                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      OUTPUT GENERATOR (Stage 5)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Generate complete trade specifications for each pick:                      │
│  Entry zone, SL, Targets, Confidence, Warnings, Audit trail                │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. MomentumGate

Filters candidates based on minimum momentum and volume thresholds.

```typescript
interface MomentumGateInput {
  symbol: string;
  priceHistory: number[];      // Last 20 sessions
  volumeHistory: number[];     // Last 20 sessions
}

interface MomentumGateOutput {
  passed: boolean;
  movePercent: number;         // Max move in 5-10 session window
  volumeMultiplier: number;    // Current vs 20-day avg
  rejectionReason?: string;
}

function applyMomentumGate(input: MomentumGateInput): MomentumGateOutput {
  const move = calculateMaxMove(input.priceHistory, 5, 10);
  const volumeMultiplier = calculateVolumeMultiplier(input.volumeHistory);
  
  // REJECT only if BOTH conditions fail
  const passed = move >= 4 || volumeMultiplier >= 1.5;
  
  return {
    passed,
    movePercent: move,
    volumeMultiplier,
    rejectionReason: passed ? undefined : 'Failed momentum gate: <4% move AND <1.5× volume'
  };
}
```

### 2. ScoringEngine

Calculates normalized scores for each factor.

```typescript
interface ScoringFactors {
  momentum: number;      // 0-100, weight: 25%
  volume: number;        // 0-100, weight: 20%
  sectorStrength: number;// 0-100, weight: 15%
  technical: number;     // 0-100, weight: 15%
  flow: number;          // 0-100, weight: 15%
  sentiment: number;     // 0-100, weight: 10%
}

interface ScoringWeights {
  momentum: 0.25;
  volume: 0.20;
  sectorStrength: 0.15;
  technical: 0.15;
  flow: 0.15;
  sentiment: 0.10;
}

function calculateWeightedScore(factors: ScoringFactors): number {
  return (
    factors.momentum * 0.25 +
    factors.volume * 0.20 +
    factors.sectorStrength * 0.15 +
    factors.technical * 0.15 +
    factors.flow * 0.15 +
    factors.sentiment * 0.10
  );
}
```

### 3. NormalizationFunctions

```typescript
// Momentum: 0% → 0, 10%+ → 100
function normalizeMomentum(movePercent: number): number {
  return Math.min(100, Math.max(0, movePercent * 10));
}

// Volume: 1× → 0, 3×+ → 100
function normalizeVolume(multiplier: number): number {
  return Math.min(100, Math.max(0, (multiplier - 1) * 50));
}

// Sector: -2% vs NIFTY → 0, +2% vs NIFTY → 100
function normalizeSectorStrength(relativePerformance: number): number {
  return Math.min(100, Math.max(0, (relativePerformance + 2) * 25));
}

// Flow: Combines FII/DII direction and delivery %
function normalizeFlow(fiiNet: number, diiNet: number, deliveryPercent: number): number {
  const flowDirection = (fiiNet > 0 ? 25 : 0) + (diiNet > 0 ? 25 : 0);
  const deliveryScore = Math.min(50, deliveryPercent);
  return flowDirection + deliveryScore;
}

// Sentiment: -100 to +100 Twitter → 0 to 100
function normalizeSentiment(twitterScore: number): number {
  return Math.min(100, Math.max(0, (twitterScore + 100) / 2));
}
```

### 4. TwitterScout

Non-authoritative confirmation layer.

```typescript
interface TwitterSignal {
  symbol: string;
  isTrending: boolean;
  sentimentScore: number;    // -100 to +100
  mentionCount: number;
  topThemes: string[];
}

interface TwitterAdjustment {
  confidenceBoost: number;   // 0, 5, or 10
  isHypeOnly: boolean;       // True if trending but no price/volume confirmation
  warning?: string;
}

function evaluateTwitterSignal(
  signal: TwitterSignal,
  hasMomentumConfirmation: boolean,
  hasVolumeConfirmation: boolean
): TwitterAdjustment {
  // Trending + confirmed = boost
  if (signal.isTrending && hasMomentumConfirmation && hasVolumeConfirmation) {
    return {
      confidenceBoost: signal.sentimentScore > 50 ? 10 : 5,
      isHypeOnly: false
    };
  }
  
  // Trending but no confirmation = hype
  if (signal.isTrending && (!hasMomentumConfirmation || !hasVolumeConfirmation)) {
    return {
      confidenceBoost: 0,
      isHypeOnly: true,
      warning: 'Twitter trending without price/volume confirmation - treated as hype'
    };
  }
  
  // Negative sentiment = warning only
  if (signal.sentimentScore < -30) {
    return {
      confidenceBoost: 0,
      isHypeOnly: false,
      warning: 'Negative Twitter sentiment detected'
    };
  }
  
  return { confidenceBoost: 0, isHypeOnly: false };
}
```

### 5. SectorAnalyzer

```typescript
interface SectorPerformance {
  sectorName: string;
  returnVsNifty: number;     // 5-session relative return
  isOutperforming: boolean;  // returnVsNifty > 0.5%
  topStocks: string[];
}

interface StockSectorAnalysis {
  symbol: string;
  sector: string;
  stockReturn: number;
  sectorReturn: number;
  niftyReturn: number;
  vsNifty: number;
  vsSector: number;
  adjustmentPercent: number; // Penalty or boost
}

function analyzeStockVsSector(
  stockReturn: number,
  sectorReturn: number,
  niftyReturn: number
): number {
  let adjustment = 0;
  
  // Underperforming sector
  if (stockReturn < sectorReturn) {
    adjustment -= 12; // -10% to -15% range, use midpoint
  }
  
  // Underperforming NIFTY
  if (stockReturn < niftyReturn) {
    adjustment -= 7; // -5% to -10% range, use midpoint
  }
  
  // Outperforming both
  if (stockReturn > sectorReturn && stockReturn > niftyReturn) {
    adjustment += 10;
  }
  
  return adjustment;
}
```

### 6. VolumeValidator

```typescript
interface VolumeValidation {
  isValidMomentum: boolean;
  isPotentialDistribution: boolean;
  isSuspicious: boolean;
  deliveryBoost: number;
  adjustmentPercent: number;
}

function validateVolume(
  volumeMultiplier: number,
  priceChange: number,
  previousPriceDirection: number,
  deliveryPercent: number
): VolumeValidation {
  const isHighVolume = volumeMultiplier > 2;
  const isTrendContinuation = Math.sign(priceChange) === Math.sign(previousPriceDirection);
  const hasSignificantMove = Math.abs(priceChange) > 2;
  
  // High volume + trend continuation = valid momentum
  if (isHighVolume && isTrendContinuation && hasSignificantMove) {
    return {
      isValidMomentum: true,
      isPotentialDistribution: false,
      isSuspicious: false,
      deliveryBoost: deliveryPercent > 50 ? 5 : 0,
      adjustmentPercent: deliveryPercent > 50 ? 5 : 0
    };
  }
  
  // High volume + reversal = potential distribution
  if (isHighVolume && !isTrendContinuation) {
    return {
      isValidMomentum: false,
      isPotentialDistribution: true,
      isSuspicious: false,
      deliveryBoost: 0,
      adjustmentPercent: -15
    };
  }
  
  // High volume + no price move = suspicious
  if (isHighVolume && !hasSignificantMove) {
    return {
      isValidMomentum: false,
      isPotentialDistribution: false,
      isSuspicious: true,
      deliveryBoost: 0,
      adjustmentPercent: -10
    };
  }
  
  return {
    isValidMomentum: false,
    isPotentialDistribution: false,
    isSuspicious: false,
    deliveryBoost: 0,
    adjustmentPercent: 0
  };
}
```

### 7. FinalRanker

```typescript
interface RankedStock {
  symbol: string;
  name: string;
  baseScore: number;
  adjustedScore: number;
  sector: string;
  sectorOutperforming: boolean;
  warnings: string[];
}

function rankAndSelect(
  candidates: RankedStock[],
  minOutperformingSectorStocks: number = 3
): RankedStock[] {
  // Sort by adjusted score
  const sorted = [...candidates].sort((a, b) => b.adjustedScore - a.adjustedScore);
  
  // Ensure sector representation
  const outperformingStocks = sorted.filter(s => s.sectorOutperforming);
  const otherStocks = sorted.filter(s => !s.sectorOutperforming);
  
  const result: RankedStock[] = [];
  
  // First, add top stocks from outperforming sectors (up to 3 per sector)
  const sectorCounts: Record<string, number> = {};
  for (const stock of outperformingStocks) {
    if (result.length >= 10) break;
    sectorCounts[stock.sector] = (sectorCounts[stock.sector] || 0) + 1;
    if (sectorCounts[stock.sector] <= 3) {
      result.push(stock);
    }
  }
  
  // Fill remaining slots with other stocks
  for (const stock of otherStocks) {
    if (result.length >= 10) break;
    sectorCounts[stock.sector] = (sectorCounts[stock.sector] || 0) + 1;
    if (sectorCounts[stock.sector] <= 3) {
      result.push(stock);
    }
  }
  
  // Re-sort final list by score
  return result.sort((a, b) => b.adjustedScore - a.adjustedScore);
}
```

## Data Models

### StockCandidate

```typescript
interface StockCandidate {
  symbol: string;
  name: string;
  sector: string;
  
  // Price data
  currentPrice: number;
  priceHistory: number[];      // Last 20 sessions
  move5to10Sessions: number;   // Max % move in window
  
  // Volume data
  volumeHistory: number[];     // Last 20 sessions
  volumeMultiplier: number;    // vs 20-day avg
  deliveryPercent: number;
  
  // Sector data
  sectorReturn: number;        // 5-session
  niftyReturn: number;         // 5-session
  stockReturn: number;         // 5-session
  
  // Technical
  patternConfidence: number;   // From vision agent
  supportLevels: number[];
  resistanceLevels: number[];
  
  // Flow
  fiiNetBuy: number;
  diiNetBuy: number;
  
  // Twitter
  twitterSignal: TwitterSignal;
}
```

### FinalPick

```typescript
interface FinalPick {
  id: string;
  symbol: string;
  name: string;
  direction: 'LONG' | 'SHORT';
  
  // Trade levels
  entryZone: { low: number; high: number };
  stopLoss: number;
  target1: number;
  target2: number;
  expectedMove: number;
  
  // Scores
  confidence: number;          // Final adjusted score
  scoringBreakdown: {
    momentum: { raw: number; normalized: number; weighted: number };
    volume: { raw: number; normalized: number; weighted: number };
    sectorStrength: { raw: number; normalized: number; weighted: number };
    technical: { raw: number; normalized: number; weighted: number };
    flow: { raw: number; normalized: number; weighted: number };
    sentiment: { raw: number; normalized: number; weighted: number };
  };
  
  // Context
  sector: string;
  sectorStrength: number;
  volumeMultiplier: number;
  
  // Twitter
  twitterStatus: 'trending' | 'not_trending' | 'negative';
  twitterBoost: number;
  
  // Warnings
  warnings: string[];
  
  // Audit
  auditTrail: AuditEntry[];
}
```

### AuditEntry

```typescript
interface AuditEntry {
  timestamp: string;
  stage: 'gate' | 'scoring' | 'adjustment' | 'ranking' | 'output';
  action: string;
  details: Record<string, any>;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Momentum Gate Consistency

*For any* stock candidate, if the stock has a move ≥4% in the 5-10 session window OR volume ≥1.5× the 20-day average, then the momentum gate SHALL pass the stock. Conversely, if BOTH conditions fail, the stock SHALL be rejected.

**Validates: Requirements 1.1, 1.2, 1.4**

### Property 2: Weighted Score Calculation

*For any* set of normalized scoring factors (each 0-100), the weighted score SHALL equal: momentum×0.25 + volume×0.20 + sectorStrength×0.15 + technical×0.15 + flow×0.15 + sentiment×0.10, and the result SHALL be in the range [0, 100].

**Validates: Requirements 4.1, 4.3**

### Property 3: Normalization Bounds

*For any* raw input value, all normalization functions SHALL produce output in the range [0, 100], regardless of input extremes.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**

### Property 4: Twitter Cannot Override Momentum Gate

*For any* stock that fails the momentum gate, the stock SHALL be rejected regardless of Twitter trending status or sentiment score.

**Validates: Requirements 5.2, 5.3, 8.1, 8.4**

### Property 5: Sector Representation Minimum

*For any* final Top 10 output where at least 3 stocks from outperforming sectors passed all gates, the output SHALL contain at least 3 stocks from outperforming sectors.

**Validates: Requirements 3.1, 3.2**

### Property 6: Sector Diversification Maximum

*For any* final Top 10 output, no single sector SHALL have more than 3 stocks represented.

**Validates: Requirements 3.4**

### Property 7: Score Ordering

*For any* final Top 10 output, stocks SHALL be ordered by adjusted confidence score in descending order. If two stocks have equal scores, the one with higher volume expansion SHALL rank first.

**Validates: Requirements 4.2, 7.3**

### Property 8: Volume Validation Classification

*For any* stock with volume >2× average, if price moved >2% in the same direction as the previous trend, it SHALL be classified as "valid momentum". If price reversed, it SHALL be classified as "potential distribution".

**Validates: Requirements 6.1, 6.2**

### Property 9: Twitter Hype Detection

*For any* stock trending on Twitter, if the stock lacks price momentum confirmation (<4% move) AND lacks volume confirmation (<1.5× average), it SHALL be flagged as "hype only" and excluded from the Top 10.

**Validates: Requirements 5.2, 8.4**

### Property 10: Audit Completeness

*For any* stock evaluated by the Decision Engine, the audit trail SHALL contain entries for each stage: gate, scoring, adjustment, ranking, and (if selected) output.

**Validates: Requirements 10.1, 10.4**

## Error Handling

### Gate Failures
- Log rejection reason with full context
- Include in rejected stocks list for audit
- Never silently drop candidates

### Data Quality Issues
- Missing price data: Reject with "INSUFFICIENT_DATA"
- Missing volume data: Use available data, flag as "PARTIAL_DATA"
- Missing Twitter data: Score sentiment as neutral (50)

### Calculation Errors
- Division by zero in normalization: Return 0 with warning
- Negative values where unexpected: Clamp to 0 with warning
- Values exceeding bounds: Clamp to bounds with warning

### System Errors
- Agent timeout: Use cached data if <1 hour old, else exclude factor
- API failure: Retry 3 times, then fail gracefully with partial output

## Testing Strategy

### Unit Tests
- Test each normalization function with boundary values
- Test momentum gate with edge cases (exactly 4%, exactly 1.5×)
- Test weighted score calculation accuracy
- Test sector adjustment calculations
- Test Twitter evaluation logic

### Property-Based Tests
Property-based testing validates universal properties across many generated inputs. Each property test runs minimum 100 iterations.

1. **Momentum Gate Property Test**
   - Generate random price/volume histories
   - Verify gate decision matches specification
   - **Feature: momentum-decision-engine, Property 1: Momentum Gate Consistency**

2. **Weighted Score Property Test**
   - Generate random factor values (0-100)
   - Verify weighted sum equals expected formula
   - Verify result is always in [0, 100]
   - **Feature: momentum-decision-engine, Property 2: Weighted Score Calculation**

3. **Normalization Bounds Property Test**
   - Generate extreme input values (-1000 to +1000)
   - Verify all outputs are in [0, 100]
   - **Feature: momentum-decision-engine, Property 3: Normalization Bounds**

4. **Twitter Override Property Test**
   - Generate stocks that fail momentum gate
   - Add various Twitter signals
   - Verify all are still rejected
   - **Feature: momentum-decision-engine, Property 4: Twitter Cannot Override**

5. **Sector Representation Property Test**
   - Generate candidate pools with varying sector distributions
   - Verify minimum 3 from outperforming sectors when available
   - **Feature: momentum-decision-engine, Property 5: Sector Representation Minimum**

6. **Sector Diversification Property Test**
   - Generate candidate pools with sector clustering
   - Verify no sector exceeds 3 stocks in output
   - **Feature: momentum-decision-engine, Property 6: Sector Diversification Maximum**

7. **Score Ordering Property Test**
   - Generate random scored candidates
   - Verify output is sorted correctly
   - **Feature: momentum-decision-engine, Property 7: Score Ordering**

8. **Volume Validation Property Test**
   - Generate high-volume scenarios with various price movements
   - Verify classification matches specification
   - **Feature: momentum-decision-engine, Property 8: Volume Validation Classification**

9. **Twitter Hype Property Test**
   - Generate trending stocks without momentum/volume confirmation
   - Verify all are flagged as hype and excluded
   - **Feature: momentum-decision-engine, Property 9: Twitter Hype Detection**

10. **Audit Completeness Property Test**
    - Process random candidates through full pipeline
    - Verify audit trail contains all required stages
    - **Feature: momentum-decision-engine, Property 10: Audit Completeness**

### Integration Tests
- End-to-end pipeline with mock data
- Verify output format matches specification
- Test with real market data samples (historical)
