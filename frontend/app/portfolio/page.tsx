"use client";
import { useEffect, useState } from "react";
import { getPortfolio, getPerformance, PortfolioState, PerformanceData } from "@/lib/api";

export default function PortfolioPage() {
  const [data, setData] = useState<PortfolioState | null>(null);
  const [perf, setPerf] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getPortfolio(), getPerformance()])
      .then(([p, pf]) => {
        setData(p);
        setPerf(pf);
      })
      .finally(() => setLoading(false));

    const i = setInterval(() => {
      Promise.all([getPortfolio(), getPerformance()]).then(([p, pf]) => {
        setData(p);
        setPerf(pf);
      });
    }, 30_000);
    return () => clearInterval(i);
  }, []);

  if (loading) return <div className="h-96 bg-[var(--bg-card)] rounded-lg loading-shimmer" />;
  if (!data) return <div className="text-[var(--text-muted)]">Failed to load portfolio.</div>;

  const cap = data.capital;
  const intel = data.intelligence;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end border-b border-[var(--border-default)] pb-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight uppercase">Positions</h1>
          <p className="text-xs text-[var(--text-muted)] font-mono mt-1">REAL-TIME PORTFOLIO TRACKING</p>
        </div>
      </div>

      <div className="bg-blue-900/20 border border-blue-500/30 p-3 rounded-md flex items-center gap-3">
        <span className="text-blue-400 text-lg">ℹ️</span>
        <p className="text-xs text-blue-200/80 font-medium">
          <strong className="text-blue-400 font-bold uppercase tracking-wider">System-Generated Portfolio: </strong> 
          This is a simulated paper-trading environment. It tracks the theoretical performance of the AI's trade recommendations to validate the system's accuracy, and is not linked to your actual brokerage account.
        </p>
      </div>

      {/* Top Summary Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        <StatBox label="Current Capital" value={`₹${cap.current.toLocaleString("en-IN")}`} />
        <StatBox label="Total Equity" value={`₹${cap.total_equity.toLocaleString("en-IN")}`}
          color={cap.total_equity >= cap.initial ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"} />
        <StatBox label="Unrealized P&L" value={`${cap.unrealized_pnl >= 0 ? "+" : ""}₹${cap.unrealized_pnl.toFixed(0)}`}
          color={cap.unrealized_pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"} />
        <StatBox label="Daily Change" value={`${cap.unrealized_pnl >= 0 ? "+" : ""}${(cap.unrealized_pnl / cap.initial * 100).toFixed(2)}%`}
          color={cap.unrealized_pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"} />
        {perf && (
          <>
            <StatBox label="Win Rate" value={`${(perf.win_rate * 100).toFixed(1)}%`} color="text-white" />
            <StatBox label="Profit Factor" value={perf.profit_factor.toFixed(2)} color="text-white" />
          </>
        )}
      </div>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Positions Data Grid (75%) */}
        <div className="lg:w-[75%]">
          <h2 className="text-xs font-bold text-[var(--text-muted)] tracking-widest uppercase mb-3">
            Open Positions ({data.positions.length}/{data.exposure.max_active_trades})
          </h2>

          {data.positions.length > 0 ? (
            <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-md overflow-x-auto">
              <table className="w-full min-w-[800px] text-[12px]">
                <thead className="bg-[var(--bg-secondary)] border-b border-[var(--border-default)] text-[10px] text-[var(--text-muted)] uppercase tracking-wider">
                  <tr>
                    <th className="text-left py-2 px-4 font-semibold">Symbol</th>
                    <th className="text-left py-2 px-4 font-semibold">Side</th>
                    <th className="text-right py-2 px-4 font-semibold">Entry</th>
                    <th className="text-right py-2 px-4 font-semibold">Current</th>
                    <th className="text-right py-2 px-4 font-semibold">Size</th>
                    <th className="text-right py-2 px-4 font-semibold">PnL $</th>
                    <th className="text-right py-2 px-4 font-semibold">PnL %</th>
                    <th className="text-center py-2 px-4 font-semibold">Stop Loss</th>
                    <th className="text-center py-2 px-4 font-semibold">Target</th>
                  </tr>
                </thead>
                <tbody className="font-mono text-[11px]">
                  {data.positions.map((p, i) => (
                    <tr key={p.trade_id} className={`hover:bg-[var(--bg-secondary)]/50 ${i % 2 === 0 ? "bg-[var(--bg-primary)]" : "bg-[var(--bg-card)]"}`}>
                      <td className="py-2.5 px-4 font-bold text-white">{p.symbol}</td>
                      <td className="py-2.5 px-4 text-[var(--accent-green)]">LONG</td>
                      <td className="py-2.5 px-4 text-right">₹{p.entry_price.toFixed(1)}</td>
                      <td className="py-2.5 px-4 text-right text-white">₹{p.current_price.toFixed(1)}</td>
                      <td className="py-2.5 px-4 text-right text-[var(--text-secondary)]">{p.position_size}</td>
                      <td className={`py-2.5 px-4 text-right font-medium ${
                        p.unrealized_pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
                      }`}>
                        {p.unrealized_pnl >= 0 ? "+" : ""}₹{p.unrealized_pnl.toFixed(0)}
                      </td>
                      <td className={`py-2.5 px-4 text-right ${
                        p.unrealized_pnl_pct >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
                      }`}>
                        {p.unrealized_pnl_pct >= 0 ? "+" : ""}{p.unrealized_pnl_pct.toFixed(2)}%
                      </td>
                      <td className="py-2.5 px-4 text-center text-[var(--accent-red)]">₹{p.stop_loss.toFixed(1)}</td>
                      <td className="py-2.5 px-4 text-center text-[var(--accent-green)]">₹{p.target.toFixed(1)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-md p-12 text-center text-[var(--text-muted)] text-sm font-mono border-dashed">
              NO OPEN POSITIONS.
            </div>
          )}
        </div>

        {/* Exposure/Chart Section (25%) */}
        <div className="lg:w-[25%] space-y-4">
          <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-md p-4">
            <h2 className="text-xs font-bold text-[var(--text-muted)] tracking-widest uppercase mb-4">Risk Exposure</h2>
            <div className="flex items-center justify-center py-6 relative">
              <svg viewBox="0 0 36 36" className="w-32 h-32 transform -rotate-90">
                <path
                  className="text-[var(--bg-secondary)]"
                  strokeWidth="4"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
                <path
                  className="text-[var(--accent-blue)] drop-shadow-[0_0_8px_var(--accent-blue)]"
                  strokeDasharray={`${data.exposure.total_exposure_pct}, 100`}
                  strokeWidth="4"
                  strokeLinecap="round"
                  stroke="currentColor"
                  fill="none"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-xl font-mono font-bold text-white">{data.exposure.total_exposure_pct}%</span>
                <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)]">Invested</span>
              </div>
            </div>
            <div className="text-center mt-2 font-mono text-[11px] text-[var(--text-secondary)]">
              Max limit: {intel.max_exposure_dynamic}%
            </div>
          </div>

          {Object.keys(data.exposure.sector_breakdown).length > 0 && (
            <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-md p-4">
              <h2 className="text-xs font-bold text-[var(--text-muted)] tracking-widest uppercase mb-4">Sectors</h2>
              <div className="space-y-4">
                {Object.entries(data.exposure.sector_breakdown).map(([sector, info]) => (
                  <div key={sector}>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-[11px] text-white uppercase tracking-wider">{sector}</span>
                      <span className="text-[10px] font-mono text-[var(--text-secondary)]">{info.exposure_pct}%</span>
                    </div>
                    <div className="h-1 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          info.exposure_pct > 20 ? "bg-[var(--accent-yellow)]" : "bg-[var(--accent-blue)]"
                        }`}
                        style={{ width: `${Math.min(100, (info.exposure_pct / 25) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatBox({ label, value, color = "text-white" }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-md p-3 relative overflow-hidden group">
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
      <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wider block mb-1 font-semibold">{label}</span>
      <span className={`text-lg font-bold font-mono ${color}`}>{value}</span>
    </div>
  );
}
