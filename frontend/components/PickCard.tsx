"use client";
import { TradeDecision } from "@/lib/api";
import Link from "next/link";

export default function PickCard({ pick }: { pick: TradeDecision }) {
  const pWin = (pick.probability * 100).toFixed(0);
  const rr = pick.risk_reward?.toFixed(1) || "–";
  const isAccept = pick.decision === "ACCEPT";

  // Mock reasons and risks since they might not be fully structured in the API yet
  const reasons = [
    "Sector Strength",
    pick.score > 70 ? "High Momentum" : "Value Setup"
  ];
  
  const risks = [
    "Market Volatility",
    pick.probability < 0.6 ? "Low Conviction" : null
  ].filter(Boolean);

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

        {/* Logic / Reasons */}
        <div className="flex-1 space-y-4 mb-4">
          <div>
            <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold flex items-center gap-1.5 mb-2">
              <span className="text-[12px]">🧠</span> Why this trade
            </span>
            <ul className="space-y-1.5">
              {reasons.map((r, i) => (
                <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                  <span className="text-[var(--accent-green)] mt-0.5">✔</span> {r}
                </li>
              ))}
            </ul>
          </div>
          
          {risks.length > 0 && (
            <div>
              <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold flex items-center gap-1.5 mb-2">
                <span className="text-[12px]">⚠</span> Risks
              </span>
              <ul className="space-y-1.5">
                {risks.map((r, i) => (
                  <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                    <span className="text-[var(--accent-red)] mt-0.5">•</span> {r}
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
