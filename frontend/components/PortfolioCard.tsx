"use client";
import { PortfolioState } from "@/lib/api";

export default function PortfolioCard({ data }: { data: PortfolioState }) {
  const cap = data.capital;
  const intel = data.intelligence;
  const exp = data.exposure;

  const regimeColor = intel.regime === "trending" ? "text-[var(--accent-green)]" :
                      intel.regime === "volatile" ? "text-[var(--accent-red)]" :
                      "text-[var(--accent-yellow)]";

  return (
    <div className="p-5">
      <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-widest mb-4 flex items-center gap-2">
        <span>💰</span> Portfolio
      </h3>

      {/* Capital row */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <span className="text-[11px] text-[var(--text-muted)] block">Equity</span>
          <span className="text-lg font-semibold font-mono text-white">
            ₹{cap.total_equity.toLocaleString("en-IN")}
          </span>
        </div>
        <div>
          <span className="text-[11px] text-[var(--text-muted)] block">Unrealized P&L</span>
          <span className={`text-lg font-semibold font-mono ${
            cap.unrealized_pnl >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
          }`}>
            {cap.unrealized_pnl >= 0 ? "+" : ""}₹{cap.unrealized_pnl.toFixed(0)}
          </span>
        </div>
      </div>

      {/* Exposure bar */}
      <div className="mb-4">
        <div className="flex justify-between text-[11px] mb-1">
          <span className="text-[var(--text-muted)]">Exposure</span>
          <span className="font-mono text-white">{exp.total_exposure_pct.toFixed(1)}% / {exp.max_total_exposure_pct}%</span>
        </div>
        <div className="h-2 bg-[var(--bg-primary)] rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full ${
              exp.total_exposure_pct > 60 ? "bg-[var(--accent-red)]" :
              exp.total_exposure_pct > 40 ? "bg-[var(--accent-yellow)]" :
              "bg-[var(--accent-blue)]"
            }`}
            style={{ width: `${Math.min(100, (exp.total_exposure_pct / exp.max_total_exposure_pct) * 100)}%` }}
          />
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-3 gap-3 text-[11px]">
        <div>
          <span className="text-[var(--text-muted)] block">Positions</span>
          <span className="font-mono text-white font-medium">{data.summary.open_positions}/{exp.max_active_trades}</span>
        </div>
        <div>
          <span className="text-[var(--text-muted)] block">Regime</span>
          <span className={`font-medium capitalize ${regimeColor}`}>{intel.regime}</span>
        </div>
        <div>
          <span className="text-[var(--text-muted)] block">Portfolio EV</span>
          <span className="font-mono text-[var(--accent-green)]">₹{intel.portfolio_EV.toFixed(0)}</span>
        </div>
      </div>

      {/* Sector breakdown */}
      {Object.keys(exp.sector_breakdown).length > 0 && (
        <div className="mt-4 pt-3 border-t border-[var(--border-default)]">
          <span className="text-[11px] text-[var(--text-muted)] block mb-2">Sectors</span>
          <div className="space-y-1.5">
            {Object.entries(exp.sector_breakdown).map(([sector, info]) => (
              <div key={sector} className="flex items-center justify-between text-[11px]">
                <span className="text-[var(--text-secondary)]">{sector}</span>
                <div className="flex items-center gap-2">
                  <div className="w-16 h-1 bg-[var(--bg-primary)] rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        info.exposure_pct > 20 ? "bg-[var(--accent-yellow)]" : "bg-[var(--accent-blue)]"
                      }`}
                      style={{ width: `${Math.min(100, (info.exposure_pct / 25) * 100)}%` }}
                    />
                  </div>
                  <span className="font-mono text-white w-10 text-right">{info.exposure_pct}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
