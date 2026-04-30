"use client";
import { TradeDecision } from "@/lib/api";
import Link from "next/link";
import { Lightbulb, AlertTriangle, TrendingUp, Shield, BarChart3 } from "lucide-react";

// ── Helpers to extract structured reasons & risks from backend data ──

function extractReasons(pick: TradeDecision): string[] {
  const reasons: string[] = [];
  const agents = pick.agents as Record<string, Record<string, unknown>> | undefined;
  const features = pick.features;

  // 1. Pattern analysis (stock-specific)
  if (agents?.pattern) {
    const patternType = agents.pattern.type as string;
    const patternScore = agents.pattern.score as number;
    if (patternType && patternType !== "none" && patternType !== "unknown") {
      const strength = patternScore >= 0.7 ? "Strong" : patternScore >= 0.5 ? "Moderate" : "Weak";
      reasons.push(`${strength} ${formatPatternName(patternType)} pattern detected`);
    }
  }

  // 2. Sector strength (stock-specific)
  if (agents?.sector) {
    const sectorScore = agents.sector.score as number;
    const sectorName = agents.sector.sector as string || pick.sector;
    if (sectorScore >= 0.6) {
      reasons.push(`${sectorName} sector showing relative strength`);
    } else if (sectorScore >= 0.45) {
      reasons.push(`${sectorName} sector in neutral territory`);
    }
  }

  // 3. Feature-based reasons (stock-specific scores)
  if (features) {
    if (features.VC >= 0.6) reasons.push("Volume confirming the move");
    if (features.MA >= 0.6) reasons.push("Aligned with broader market trend");
    if (features.SE >= 0.55) reasons.push("Positive sentiment from news flow");
    if (features.LS >= 0.7) reasons.push("Strong liquidity — tight spreads");
    if (features.MR <= 0.1) reasons.push("Clean price action — no manipulation signals");
  }

  // 4. Probability-based
  if (pick.probability >= 0.7) {
    reasons.push("High conviction trade (P(win) > 70%)");
  } else if (pick.probability >= 0.6) {
    reasons.push("Moderate conviction with positive edge");
  }

  // 5. Risk:Reward based
  const rr = pick.reward_risk || pick.risk_reward;
  if (rr >= 2.0) {
    reasons.push(`Favorable R:R of ${rr.toFixed(1)}x`);
  }

  // Fallback: use backend reasoning strings directly
  if (reasons.length === 0 && pick.reasoning && pick.reasoning.length > 0) {
    return pick.reasoning.filter(r => !r.startsWith("⚠")).slice(0, 4);
  }

  return reasons.slice(0, 4);
}

function extractRisks(pick: TradeDecision): string[] {
  const risks: string[] = [];
  const agents = pick.agents as Record<string, Record<string, unknown>> | undefined;
  const features = pick.features;

  // 1. Manipulation risk (stock-specific)
  if (agents?.manipulation) {
    const mRisk = agents.manipulation.risk as number;
    if (mRisk >= 0.5) {
      risks.push("High manipulation risk in price action");
    } else if (mRisk >= 0.3) {
      risks.push("Moderate manipulation signals detected");
    }
  }

  // 2. Liquidity risk (stock-specific)
  if (agents?.liquidity) {
    const lScore = agents.liquidity.score as number;
    if (lScore < 0.4) {
      risks.push("Low liquidity — wider spreads and slippage risk");
    }
  }

  // 3. Feature-based risks
  if (features) {
    if (features.VC < 0.35) risks.push("Volume not confirming — weak participation");
    if (features.SE < 0.4) risks.push("Negative news sentiment");
    if (features.MA < 0.35) risks.push("Fighting the broader market trend");
  }

  // 4. Regime-based
  if (pick.regime === "volatile") {
    risks.push("Volatile market regime — wider stop needed");
  } else if (pick.regime === "sideways") {
    risks.push("Sideways regime — higher false breakout risk");
  }

  // 5. Conviction-based
  if (pick.probability < 0.6) {
    risks.push(`Lower conviction (P(win) = ${(pick.probability * 100).toFixed(0)}%)`);
  }

  // 6. Market bias headwind
  if (pick.market_bias === "Bearish") {
    risks.push("Bearish market bias — trading against trend");
  }

  // Fallback: use backend reasoning warnings
  if (risks.length === 0 && pick.reasoning) {
    const warnings = pick.reasoning.filter(r => r.startsWith("⚠"));
    return warnings.map(w => w.replace("⚠ ", "")).slice(0, 3);
  }

  return risks.slice(0, 3);
}

function formatPatternName(pattern: string): string {
  return pattern
    .replace(/_/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase());
}

// ── Component ────────────────────────────────────────────────────────

export default function PickCard({ pick }: { pick: TradeDecision }) {
  const pWin = (pick.probability * 100).toFixed(0);
  const rr = (pick.reward_risk || pick.risk_reward)?.toFixed(1) || "–";
  const isAccept = pick.decision === "ACCEPT";

  const reasons = extractReasons(pick);
  const risks = extractRisks(pick);

  return (
    <Link href={`/trade/${pick.symbol}`} className="block h-full">
      <div className={`h-full terminal-card rounded-xl p-5 flex flex-col group ${isAccept ? "glow-accept" : ""}`}>
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-value flex items-center gap-2 group-hover:text-[var(--accent-blue)] transition-colors">
              {pick.symbol}
            </h3>
            <span className="text-label mt-1 block">
              {pick.sector}
            </span>
          </div>
          <div className="flex flex-col items-end gap-1">
            <span className={`text-[10px] font-bold px-2.5 py-1 rounded-sm uppercase tracking-wider ${
              isAccept ? "badge-accept" : "badge-reject"
            }`}>
              {pick.decision} {pick.probability >= 0.7 ? "● HIGH" : pick.probability >= 0.5 ? "● MED" : "● LOW"}
            </span>
          </div>
        </div>

        {/* Probability bar */}
        <div className="mb-5 bg-[var(--bg-secondary)]/50 p-3 rounded-lg border border-[var(--border-default)]">
          <div className="flex justify-between items-center mb-2">
            <span className="text-label">P(win)</span>
            <span className={`font-mono text-sm font-bold ${
              pick.probability >= 0.7 ? "text-[var(--accent-green-light)]" :
              pick.probability >= 0.5 ? "text-[var(--accent-yellow)]" :
              "text-[var(--accent-red-light)]"
            }`}>
              {pWin}%
            </span>
          </div>
          <div className="h-1.5 bg-[var(--bg-primary)] rounded-full overflow-hidden shadow-inner">
            <div
              className={`h-full rounded-full transition-all duration-1000 ease-out ${
                pick.probability >= 0.7 ? "bg-[var(--accent-green)]" :
                pick.probability >= 0.5 ? "bg-[var(--accent-yellow)]" :
                "bg-[var(--accent-red)]"
              }`}
              style={{ width: `${Math.min(100, pick.probability * 100)}%` }}
            />
          </div>
        </div>

        {/* Metrics grid */}
        <div className="grid grid-cols-3 gap-3 mb-5 border-b border-[var(--border-default)] pb-4">
          <div>
            <span className="text-label block mb-1">Entry</span>
            <span className="font-mono text-white text-sm">₹{pick.entry.toFixed(1)}</span>
          </div>
          <div>
            <span className="text-label block mb-1">SL</span>
            <span className="font-mono text-[var(--accent-red-light)] text-sm">₹{pick.stop_loss.toFixed(1)}</span>
          </div>
          <div>
            <span className="text-label block mb-1">Target</span>
            <span className="font-mono text-[var(--accent-green-light)] text-sm">₹{pick.target.toFixed(1)}</span>
          </div>
        </div>

        {/* Logic / Reasons — now using REAL per-stock data */}
        <div className="flex-1 space-y-4 mb-4">
          {reasons.length > 0 && (
            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold flex items-center gap-1.5 mb-2">
                <Lightbulb className="w-3 h-3" /> Why this trade
              </span>
              <ul className="space-y-1.5">
                {reasons.map((r, i) => (
                  <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                    <span className="text-[var(--accent-green)] mt-0.5 shrink-0">✔</span> {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          {risks.length > 0 && (
            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold flex items-center gap-1.5 mb-2">
                <AlertTriangle className="w-3 h-3" /> Risks
              </span>
              <ul className="space-y-1.5">
                {risks.map((r, i) => (
                  <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                    <span className="text-[var(--accent-red)] mt-0.5 shrink-0">•</span> {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center mt-auto pt-4 border-t border-[var(--border-default)]/50 bg-[var(--bg-secondary)]/20 -mx-5 -mb-5 px-5 pb-5 rounded-b-xl">
          <div>
            <span className="text-label mr-2">EV:</span>
            <span className="font-mono text-[var(--accent-green-light)] font-bold">₹{pick.ev.toFixed(1)}</span>
          </div>
          <div>
            <span className="text-label mr-2">R:R:</span>
            <span className="font-mono text-white font-medium">{rr}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}
