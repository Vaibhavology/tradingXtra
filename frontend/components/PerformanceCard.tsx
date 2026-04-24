"use client";
import { PerformanceData } from "@/lib/api";
import { BarChart2 } from "lucide-react";

export default function PerformanceCard({ data }: { data: PerformanceData }) {
  return (
    <div className="p-5">
      <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-widest mb-4 flex items-center gap-2">
        <BarChart2 className="w-4 h-4" /> Performance
      </h3>

      <div className="grid grid-cols-2 gap-3">
        <Metric label="Win Rate" value={`${((data.win_rate ?? 0) * 100).toFixed(0)}%`}
          color={(data.win_rate ?? 0) >= 0.5 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"} />
        <Metric label="Profit Factor" value={(data.profit_factor ?? 0).toFixed(2)}
          color={(data.profit_factor ?? 0) >= 1 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"} />
        <Metric label="Total PnL" value={`${(data.total_pnl ?? 0) >= 0 ? "+" : ""}₹${(data.total_pnl ?? 0).toFixed(0)}`}
          color={(data.total_pnl ?? 0) >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"} />
        <Metric label="Return" value={`${(data.return_pct ?? 0) >= 0 ? "+" : ""}${(data.return_pct ?? 0).toFixed(1)}%`}
          color={(data.return_pct ?? 0) >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"} />
        <Metric label="Max Drawdown" value={`${(data.max_drawdown_pct ?? 0).toFixed(1)}%`}
          color="text-[var(--accent-red)]" />
        <Metric label="Trades" value={`${data.closed_trades ?? 0}`} color="text-white" />
      </div>

      {data.best_trade && (
        <div className="mt-4 pt-3 border-t border-[var(--border-default)] flex justify-between text-[11px]">
          <div>
            <span className="text-[var(--text-muted)]">Best: </span>
            <span className="text-[var(--accent-green)] font-mono">
              {data.best_trade.symbol} +₹{data.best_trade.pnl.toFixed(0)}
            </span>
          </div>
          {data.worst_trade && (
            <div>
              <span className="text-[var(--text-muted)]">Worst: </span>
              <span className="text-[var(--accent-red)] font-mono">
                {data.worst_trade.symbol} ₹{data.worst_trade.pnl.toFixed(0)}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div>
      <span className="text-[11px] text-[var(--text-muted)] block">{label}</span>
      <span className={`text-sm font-semibold font-mono ${color}`}>{value}</span>
    </div>
  );
}
