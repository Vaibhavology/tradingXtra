"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getDecision, TradeDecision } from "@/lib/api";
import Link from "next/link";
import { TrendingUp, AlertTriangle, FileText } from "lucide-react";

export default function TradeDetailPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const [data, setData] = useState<TradeDecision | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol) return;
    getDecision(symbol)
      .then(setData)
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) return <div className="h-96 bg-[var(--bg-card)] rounded-lg loading-shimmer" />;
  if (error || !data) return (
    <div className="bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/20 rounded-lg p-6 text-center">
      <p className="text-[var(--accent-red)]">Failed to load {symbol}</p>
      <Link href="/" className="text-xs text-[var(--accent-blue)] mt-2 block hover:underline">← Back to Dashboard</Link>
    </div>
  );

  const agents = data.agents || {};
  const analysis = data.trade_analysis;
  const rr = data.reward_risk || data.risk_reward;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <Link href="/" className="text-xs text-[var(--text-muted)] hover:text-white mb-1 block">← Dashboard</Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">{data.symbol}</h1>
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
              data.decision === "ACCEPT" ? "badge-accept" : "badge-reject"
            }`}>
              {data.decision}
            </span>
            <span className="text-xs text-[var(--text-muted)]">{data.sector}</span>
          </div>
          <p className="text-sm text-[var(--text-secondary)] mt-1">{data.name}</p>
        </div>
      </div>

      {/* Price levels */}
      <div className="grid grid-cols-3 gap-4">
        <PriceBox label="Entry" value={data.entry} color="text-white" />
        <PriceBox label="Stop Loss" value={data.stop_loss} color="text-[var(--accent-red)]" />
        <PriceBox label="Target" value={data.target} color="text-[var(--accent-green)]" />
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricBox label="P(win)" value={`${(data.probability * 100).toFixed(1)}%`}
          color={data.probability >= 0.65 ? "text-[var(--accent-green)]" : "text-[var(--accent-yellow)]"} />
        <MetricBox label="Expected Value" value={`₹${data.ev.toFixed(2)}`}
          color={data.ev > 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"} />
        <MetricBox label="Risk:Reward" value={rr?.toFixed(2) || "–"} color="text-white" />
        <MetricBox label="ATR" value={`₹${data.atr.toFixed(2)}`} color="text-[var(--text-secondary)]" />
      </div>

      {/* Trade Thesis — Full analysis with description, pros, cons */}
      {analysis && analysis.description && (
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-5 space-y-5">
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <FileText className="w-4 h-4 text-[var(--accent-blue)]" />
            Trade Thesis
          </h2>
          
          {/* Description */}
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
            {analysis.description}
          </p>

          {/* Pros & Cons Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Pros */}
            {analysis.pros && analysis.pros.length > 0 && (
              <div className="bg-[var(--accent-green)]/5 border border-[var(--accent-green)]/15 rounded-lg p-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--accent-green)] flex items-center gap-1.5 mb-3">
                  <TrendingUp className="w-3.5 h-3.5" /> Pros
                </h3>
                <ul className="space-y-2">
                  {analysis.pros.map((pro, i) => (
                    <li key={i} className="text-[12px] text-[var(--text-secondary)] flex items-start gap-2 leading-relaxed">
                      <span className="text-[var(--accent-green)] mt-0.5 shrink-0">✔</span>
                      {pro}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Cons */}
            {analysis.cons && analysis.cons.length > 0 && (
              <div className="bg-[var(--accent-red)]/5 border border-[var(--accent-red)]/15 rounded-lg p-4">
                <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--accent-red)] flex items-center gap-1.5 mb-3">
                  <AlertTriangle className="w-3.5 h-3.5" /> Cons
                </h3>
                <ul className="space-y-2">
                  {analysis.cons.map((con, i) => (
                    <li key={i} className="text-[12px] text-[var(--text-secondary)] flex items-start gap-2 leading-relaxed">
                      <span className="text-[var(--accent-red)] mt-0.5 shrink-0">✗</span>
                      {con}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Score + Regime */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-5">
          <h2 className="text-sm font-semibold text-white mb-3">📊 Decision Score</h2>
          <div className="mb-3">
            <div className="flex justify-between text-[12px] mb-1">
              <span className="text-[var(--text-muted)]">Weighted Score</span>
              <span className="font-mono text-white">{data.score.toFixed(4)}</span>
            </div>
            <div className="h-2 bg-[var(--bg-primary)] rounded-full overflow-hidden">
              <div className="h-full bg-[var(--accent-blue)] rounded-full" style={{ width: `${data.score * 100}%` }} />
            </div>
          </div>
          <div className="text-[12px]">
            <span className="text-[var(--text-muted)]">Regime: </span>
            <span className={`capitalize font-medium ${
              data.regime === "trending" ? "text-[var(--accent-green)]" :
              data.regime === "volatile" ? "text-[var(--accent-red)]" :
              "text-[var(--accent-yellow)]"
            }`}>{data.regime}</span>
          </div>
          {data.rejection_reason && (
            <div className="mt-3 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/20 rounded p-2">
              <span className="text-[11px] text-[var(--accent-red)]">Rejection: {data.rejection_reason}</span>
            </div>
          )}
        </div>

        {/* Agent outputs */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-5">
          <h2 className="text-sm font-semibold text-white mb-3">🤖 Agent Analysis</h2>
          {Object.keys(agents).length > 0 ? (
            <div className="space-y-2">
              {Object.entries(agents).map(([agent, info]) => {
                const agentData = info as Record<string, unknown>;
                const passed = agentData.passed as boolean | undefined;
                return (
                  <div key={agent} className="flex items-center justify-between text-[12px] py-1.5 border-b border-[var(--border-default)]/50 last:border-0">
                    <span className="text-[var(--text-secondary)] capitalize">{agent.replace(/_/g, " ")}</span>
                    <div className="flex items-center gap-2">
                      {agentData.score !== undefined && (
                        <span className="font-mono text-[var(--text-muted)]">
                          {String(typeof agentData.score === "number" ? (agentData.score as number).toFixed(2) : agentData.score)}
                        </span>
                      )}
                      {agentData.risk !== undefined && (
                        <span className="font-mono text-[var(--text-muted)]">
                          {String(typeof agentData.risk === "number" ? (agentData.risk as number).toFixed(2) : agentData.risk)}
                        </span>
                      )}
                      {passed !== undefined && (
                        <span className={passed ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>
                          {passed ? "✓" : "✗"}
                        </span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-[var(--text-muted)] text-xs">No agent data available.</p>
          )}
        </div>
      </div>

      {/* Backend Reasoning (raw reasoning strings — always unique per stock) */}
      {data.reasoning && data.reasoning.length > 0 && (
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-5">
          <h2 className="text-sm font-semibold text-white mb-3">📝 System Reasoning</h2>
          <ul className="space-y-2">
            {data.reasoning.map((reason, i) => {
              const isWarning = reason.startsWith("⚠");
              return (
                <li key={i} className={`text-[12px] flex items-start gap-2 leading-relaxed ${
                  isWarning ? "text-[var(--accent-yellow)]" : "text-[var(--text-secondary)]"
                }`}>
                  <span className={`mt-0.5 shrink-0 ${isWarning ? "text-[var(--accent-yellow)]" : "text-[var(--accent-blue)]"}`}>
                    {isWarning ? "⚠" : "→"}
                  </span>
                  {reason.replace("⚠ ", "")}
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}

function PriceBox({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-4 text-center">
      <span className="text-[11px] text-[var(--text-muted)] block mb-1">{label}</span>
      <span className={`text-xl font-bold font-mono ${color}`}>₹{value.toFixed(2)}</span>
    </div>
  );
}

function MetricBox({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-3">
      <span className="text-[10px] text-[var(--text-muted)] block mb-1">{label}</span>
      <span className={`text-sm font-semibold font-mono ${color}`}>{value}</span>
    </div>
  );
}
