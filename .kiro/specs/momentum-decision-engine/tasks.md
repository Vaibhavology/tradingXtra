# Implementation Plan: Momentum-Oriented Decision Engine

## Overview

This implementation plan builds the momentum-first trading decision engine in TypeScript for the existing Next.js application. The engine will be implemented as a backend-ready module that can be integrated with the existing Trading_xtra frontend.

## Tasks

- [ ] 1. Set up core types and interfaces
  - Create `lib/engine/types.ts` with all data models
  - Define interfaces for StockCandidate, FinalPick, ScoringFactors, AuditEntry
  - Define types for TwitterSignal, SectorPerformance, VolumeValidation
  - _Requirements: 7.2, 10.1_

- [ ] 2. Implement normalization functions
  - [ ] 2.1 Create `lib/engine/normalizers.ts` with all normalization functions
    - Implement `normalizeMomentum`: 0% → 0, 10%+ → 100
    - Implement `normalizeVolume`: 1× → 0, 3×+ → 100
    - Implement `normalizeSectorStrength`: -2% → 0, +2% → 100
    - Implement `normalizeFlow`: FII/DII direction + delivery %
    - Implement `normalizeSentiment`: -100 to +100 → 0 to 100
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ] 2.2 Write property test for normalization bounds
    - **Property 3: Normalization Bounds**
    - Generate extreme input values (-1000 to +1000)
    - Verify all outputs are in [0, 100]
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**

- [ ] 3. Implement Momentum Gate
  - [ ] 3.1 Create `lib/engine/momentumGate.ts`
    - Implement `calculateMaxMove` for 5-10 session window
    - Implement `calculateVolumeMultiplier` vs 20-day average
    - Implement `applyMomentumGate` with pass/reject logic
    - Handle boundary conditions (exactly 4%, exactly 1.5×)
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ] 3.2 Write property test for momentum gate consistency
    - **Property 1: Momentum Gate Consistency**
    - Generate random price/volume histories
    - Verify: pass if move ≥4% OR volume ≥1.5×
    - Verify: reject only if BOTH conditions fail
    - **Validates: Requirements 1.1, 1.2, 1.4**

- [ ] 4. Implement Scoring Engine
  - [ ] 4.1 Create `lib/engine/scoringEngine.ts`
    - Implement `calculateWeightedScore` with correct weights
    - Momentum: 25%, Volume: 20%, Sector: 15%, Technical: 15%, Flow: 15%, Sentiment: 10%
    - Ensure all factors are normalized before weighting
    - _Requirements: 4.1, 4.3, 4.4_

  - [ ] 4.2 Write property test for weighted score calculation
    - **Property 2: Weighted Score Calculation**
    - Generate random factor values (0-100)
    - Verify weighted sum equals expected formula
    - Verify result is always in [0, 100]
    - **Validates: Requirements 4.1, 4.3**

- [ ] 5. Checkpoint - Ensure core scoring tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement Twitter Scout
  - [ ] 6.1 Create `lib/engine/twitterScout.ts`
    - Implement `evaluateTwitterSignal` function
    - Handle trending + confirmed → boost 5-10%
    - Handle trending + no confirmation → flag as hype
    - Handle negative sentiment → warning only
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ] 6.2 Write property test for Twitter cannot override
    - **Property 4: Twitter Cannot Override Momentum Gate**
    - Generate stocks that fail momentum gate
    - Add various Twitter signals (trending, high sentiment)
    - Verify all are still rejected
    - **Validates: Requirements 5.2, 5.3, 8.1, 8.4**

  - [ ] 6.3 Write property test for Twitter hype detection
    - **Property 9: Twitter Hype Detection**
    - Generate trending stocks without momentum/volume confirmation
    - Verify all are flagged as hype and excluded
    - **Validates: Requirements 5.2, 8.4**

- [ ] 7. Implement Sector Analyzer
  - [ ] 7.1 Create `lib/engine/sectorAnalyzer.ts`
    - Implement `analyzeStockVsSector` for relative performance
    - Implement `identifyOutperformingSectors` (>0.5% vs NIFTY)
    - Apply confidence adjustments: underperform penalty, outperform boost
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.3_

  - [ ] 7.2 Write unit tests for sector adjustment calculations
    - Test underperforming sector penalty (-10% to -15%)
    - Test underperforming NIFTY penalty (-5% to -10%)
    - Test outperforming boost (+10%)
    - _Requirements: 2.1, 2.2, 2.3_

- [ ] 8. Implement Volume Validator
  - [ ] 8.1 Create `lib/engine/volumeValidator.ts`
    - Implement `validateVolume` function
    - Classify: valid momentum, potential distribution, suspicious
    - Apply delivery percentage boost (>50% → +5%)
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ] 8.2 Write property test for volume validation classification
    - **Property 8: Volume Validation Classification**
    - Generate high-volume scenarios with various price movements
    - Verify: trend continuation = valid momentum
    - Verify: reversal = potential distribution
    - **Validates: Requirements 6.1, 6.2**

- [ ] 9. Checkpoint - Ensure all component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement Final Ranker
  - [ ] 10.1 Create `lib/engine/finalRanker.ts`
    - Implement `rankAndSelect` function
    - Sort by adjusted confidence score (descending)
    - Ensure ≥3 stocks from outperforming sectors
    - Limit max 3 per sector for diversification
    - Handle tiebreaker: higher volume expansion wins
    - _Requirements: 3.1, 3.4, 4.2, 7.1, 7.3_

  - [ ] 10.2 Write property test for sector representation minimum
    - **Property 5: Sector Representation Minimum**
    - Generate candidate pools with varying sector distributions
    - Verify minimum 3 from outperforming sectors when available
    - **Validates: Requirements 3.1, 3.2**

  - [ ] 10.3 Write property test for sector diversification maximum
    - **Property 6: Sector Diversification Maximum**
    - Generate candidate pools with sector clustering
    - Verify no sector exceeds 3 stocks in output
    - **Validates: Requirements 3.4**

  - [ ] 10.4 Write property test for score ordering
    - **Property 7: Score Ordering**
    - Generate random scored candidates
    - Verify output is sorted by confidence descending
    - Verify tiebreaker uses volume expansion
    - **Validates: Requirements 4.2, 7.3**

- [ ] 11. Implement Audit Trail
  - [ ] 11.1 Create `lib/engine/auditTrail.ts`
    - Implement `AuditLogger` class
    - Log raw values, normalized scores, weighted contributions
    - Log adjustments and final decisions with reasons
    - Timestamp all entries
    - _Requirements: 10.1, 10.2, 10.4_

  - [ ] 11.2 Write property test for audit completeness
    - **Property 10: Audit Completeness**
    - Process random candidates through full pipeline
    - Verify audit trail contains entries for: gate, scoring, adjustment, ranking, output
    - **Validates: Requirements 10.1, 10.4**

- [ ] 12. Implement Decision Engine Orchestrator
  - [ ] 12.1 Create `lib/engine/decisionEngine.ts`
    - Implement `MomentumDecisionEngine` class
    - Orchestrate full pipeline: gate → score → adjust → rank → output
    - Apply hard rejection rules (manipulation flags, SL risk)
    - Generate complete FinalPick objects
    - _Requirements: 7.2, 8.1, 8.2, 8.3, 8.5_

  - [ ] 12.2 Write integration test for full pipeline
    - Test end-to-end with mock data
    - Verify output format matches specification
    - Verify all fields are present
    - _Requirements: 7.2, 7.4_

- [ ] 13. Checkpoint - Ensure all engine tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Update mock data for frontend
  - [ ] 14.1 Update `lib/mockData.ts` with momentum-based picks
    - Add momentum scores and volume multipliers
    - Add sector strength data
    - Add Twitter status fields
    - Add scoring breakdown for each pick
    - _Requirements: 7.2_

- [ ] 15. Update frontend components
  - [ ] 15.1 Update `components/PickCard.tsx` to display momentum data
    - Add momentum score display
    - Add volume multiplier badge
    - Add Twitter status indicator
    - Add scoring breakdown tooltip
    - _Requirements: 7.2_

  - [ ] 15.2 Update `components/ChartModal.tsx` with momentum context
    - Add momentum analysis section
    - Add volume validation status
    - Add sector relative performance
    - _Requirements: 7.2_

- [ ] 16. Create API endpoint structure
  - [ ] 16.1 Create `app/api/engine/route.ts` (placeholder)
    - Define endpoint structure for `/api/today-picks`
    - Document request/response format
    - Add mock response using decision engine
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 17. Final checkpoint - Full system verification
  - Ensure all tests pass, ask the user if questions arise.
  - Verify frontend displays momentum data correctly
  - Verify API endpoint returns correct format

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The engine is designed to be backend-ready but runs client-side for demo purposes
