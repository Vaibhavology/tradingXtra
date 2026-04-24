"use client";
import { useEffect, useState } from "react";
import { getPerformance, PerformanceData } from "@/lib/api";
import dynamic from "next/dynamic";

const EquityChart = dynamic(() => import("@/components/EquityChart"), { ssr: false });

export default function PerformancePage() {
  const [data, setData] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPerformance().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="h-96 bg-[var(--bg-card)] rounded-lg loading-shimmer" />;
  if (!data) return <div className="text-[var(--text-muted)]">No performance data.</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold text-white">Performance</h1>

      {/* Key metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricBox label="Win Rate" value={`${((data.win_rate ?? 0) * 100).toFixed(0)}%`}
          color={(data.win_rate ?? 0) >= 0.5 ? "green" : "red"} />
        <MetricBox label="Profit Factor" value={(data.profit_factor ?? 0).toFixed(2)}
          color={(data.profit_factor ?? 0) >= 1 ? "green" : "red"} />
        <MetricBox label="Return" value={`${(data.return_pct ?? 0) >= 0 ? "+" : ""}${(data.return_pct ?? 0).toFixed(1)}%`}
          color={(data.return_pct ?? 0) >= 0 ? "green" : "red"} />
        <MetricBox label="Max Drawdown" value={`${(data.max_drawdown_pct ?? 0).toFixed(1)}%`} color="red" />
        <MetricBox label="Closed Trades" value={String(data.closed_trades ?? 0)} color="blue" />
        <MetricBox label="Total PnL" value={`₹${(data.total_pnl ?? 0).toFixed(0)}`}
          color={(data.total_pnl ?? 0) >= 0 ? "green" : "red"} />
      </div>

      {/* Equity curve */}
      {data.equity_curve && data.equity_curve.length > 0 && (
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-5">
          <h2 className="text-sm font-semibold text-white mb-4">📈 Equity Curve</h2>
          <EquityChart data={data.equity_curve} initial={data.initial_capital} />
        </div>
      )}

      {/* Win/Loss breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-5">
          <h2 className="text-sm font-semibold text-white mb-3">Win/Loss Breakdown</h2>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-[12px] mb-1">
                <span className="text-[var(--accent-green)]">Wins: {data.wins}</span>
                <span className="text-[var(--accent-red)]">Losses: {data.losses}</span>
              </div>
              <div className="h-3 bg-[var(--bg-primary)] rounded-full overflow-hidden flex">
                <div className="bg-[var(--accent-green)] h-full"
                  style={{ width: `${data.closed_trades > 0 ? (data.wins / data.closed_trades) * 100 : 0}%` }} />
                <div className="bg-[var(--accent-red)] h-full flex-1" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-[12px]">
              <div>
                <span className="text-[var(--text-muted)] block">Avg Win</span>
                <span className="font-mono text-[var(--accent-green)]">₹{(data.avg_win ?? 0).toFixed(0)}</span>
              </div>
              <div>
                <span className="text-[var(--text-muted)] block">Avg Loss</span>
                <span className="font-mono text-[var(--accent-red)]">₹{(data.avg_loss ?? 0).toFixed(0)}</span>
              </div>
              <div>
                <span className="text-[var(--text-muted)] block">Avg MFE</span>
                <span className="font-mono text-[var(--accent-green)]">₹{(data.avg_mfe ?? 0).toFixed(0)}</span>
              </div>
              <div>
                <span className="text-[var(--text-muted)] block">Avg MAE</span>
                <span className="font-mono text-[var(--accent-red)]">₹{(data.avg_mae ?? 0).toFixed(0)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Calibration */}
        {data.calibration && Object.keys(data.calibration).length > 0 && (
          <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-5">
            <h2 className="text-sm font-semibold text-white mb-3">🎯 Calibration</h2>
            <div className="space-y-2">
              {Object.entries(data.calibration).map(([bucket, info]) => (
                <div key={bucket} className="flex flex-col sm:flex-row sm:items-center justify-between text-[12px] gap-2 py-1 border-b border-[var(--border-default)]/30 last:border-0">
                  <span className="text-[var(--text-muted)] font-mono">{bucket}</span>
                  <div className="flex flex-wrap gap-x-4 gap-y-1">
                    <span>Predicted: <span className="text-[var(--accent-blue)] font-mono">{(info.predicted_avg * 100).toFixed(0)}%</span></span>
                    <span>Actual: <span className={`font-mono ${
                      info.actual_win_rate >= info.predicted_avg ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
                    }`}>{(info.actual_win_rate * 100).toFixed(0)}%</span></span>
                    <span className="text-[var(--text-muted)]">n={info.trades}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Best/Worst */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {data.best_trade && (
          <div className="bg-[var(--bg-card)] border border-[var(--accent-green)]/20 rounded-lg p-4">
            <span className="text-[11px] text-[var(--text-muted)]">Best Trade</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-white font-semibold">{data.best_trade.symbol}</span>
              <span className="text-[var(--accent-green)] font-mono font-semibold">
                +₹{data.best_trade.pnl.toFixed(0)}
              </span>
            </div>
          </div>
        )}
        {data.worst_trade && (
          <div className="bg-[var(--bg-card)] border border-[var(--accent-red)]/20 rounded-lg p-4">
            <span className="text-[11px] text-[var(--text-muted)]">Worst Trade</span>
            <div className="flex items-baseline gap-2 mt-1">
              <span className="text-white font-semibold">{data.worst_trade.symbol}</span>
              <span className="text-[var(--accent-red)] font-mono font-semibold">
                ₹{data.worst_trade.pnl.toFixed(0)}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricBox({ label, value, color }: { label: string; value: string; color: string }) {
  const c = color === "green" ? "text-[var(--accent-green)]" :
            color === "red" ? "text-[var(--accent-red)]" :
            color === "blue" ? "text-[var(--accent-blue)]" : "text-white";
  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-3">
      <span className="text-[10px] text-[var(--text-muted)] block mb-1">{label}</span>
      <span className={`text-lg font-bold font-mono ${c}`}>{value}</span>
    </div>
  );
}
