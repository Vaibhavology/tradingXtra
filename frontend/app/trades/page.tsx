"use client";
import { useEffect, useState } from "react";
import { getTrades, TradeRecord } from "@/lib/api";

export default function TradesPage() {
  const [trades, setTrades] = useState<TradeRecord[]>([]);
  const [filter, setFilter] = useState<"ALL" | "OPEN" | "CLOSED">("ALL");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getTrades().then(d => setTrades(d.trades || [])).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="h-96 bg-[var(--bg-card)] rounded-lg loading-shimmer" />;

  const filtered = filter === "ALL" ? trades :
    trades.filter(t => t.status === filter);

  const open = trades.filter(t => t.status === "OPEN").length;
  const closed = trades.filter(t => t.status === "CLOSED").length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-white">Trade Journal</h1>
        <div className="flex gap-1 bg-[var(--bg-card)] rounded-lg p-0.5 border border-[var(--border-default)]">
          {(["ALL", "OPEN", "CLOSED"] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                filter === f
                  ? "bg-[var(--accent-blue)]/15 text-[var(--accent-blue)]"
                  : "text-[var(--text-muted)] hover:text-white"
              }`}
            >
              {f} ({f === "ALL" ? trades.length : f === "OPEN" ? open : closed})
            </button>
          ))}
        </div>
      </div>

      {filtered.length > 0 ? (
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg overflow-x-auto">
          <table className="w-full text-[12px]">
            <thead>
              <tr className="border-b border-[var(--border-default)] text-[var(--text-muted)] text-[10px]">
                <th className="text-left p-3 font-medium">Symbol</th>
                <th className="text-center p-3 font-medium">Status</th>
                <th className="text-right p-3 font-medium">Entry</th>
                <th className="text-right p-3 font-medium">SL</th>
                <th className="text-right p-3 font-medium">Target</th>
                <th className="text-right p-3 font-medium">Exit</th>
                <th className="text-right p-3 font-medium">Size</th>
                <th className="text-right p-3 font-medium">PnL</th>
                <th className="text-center p-3 font-medium">P(win)</th>
                <th className="text-center p-3 font-medium">Outcome</th>
                <th className="text-left p-3 font-medium">Regime</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(t => (
                <tr key={t.id} className="border-b border-[var(--border-default)]/50 hover:bg-[var(--bg-card-hover)]">
                  <td className="p-3 font-mono font-medium text-white">{t.symbol}</td>
                  <td className="p-3 text-center">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                      t.status === "OPEN" ? "badge-open" : t.outcome === "WIN" ? "badge-win" : "badge-loss"
                    }`}>
                      {t.status}
                    </span>
                  </td>
                  <td className="p-3 text-right font-mono">₹{t.entry_price.toFixed(1)}</td>
                  <td className="p-3 text-right font-mono text-[var(--accent-red)]">₹{t.stop_loss.toFixed(1)}</td>
                  <td className="p-3 text-right font-mono text-[var(--accent-green)]">₹{t.target_price.toFixed(1)}</td>
                  <td className="p-3 text-right font-mono">{t.exit_price ? `₹${t.exit_price.toFixed(1)}` : "–"}</td>
                  <td className="p-3 text-right font-mono">{t.position_size}</td>
                  <td className={`p-3 text-right font-mono font-medium ${
                    t.pnl === null ? "text-[var(--text-muted)]" :
                    t.pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
                  }`}>
                    {t.pnl !== null ? `${t.pnl >= 0 ? "+" : ""}₹${t.pnl.toFixed(0)}` : "–"}
                  </td>
                  <td className="p-3 text-center font-mono">
                    {t.predicted_probability ? `${(t.predicted_probability * 100).toFixed(0)}%` : "–"}
                  </td>
                  <td className="p-3 text-center">
                    {t.outcome ? (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                        t.outcome === "WIN" ? "badge-win" : "badge-loss"
                      }`}>{t.outcome}</span>
                    ) : "–"}
                  </td>
                  <td className="p-3 text-[var(--text-secondary)] capitalize">{t.regime_at_entry || "–"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-8 text-center text-[var(--text-muted)] text-sm">
          No trades recorded yet.
        </div>
      )}
    </div>
  );
}
