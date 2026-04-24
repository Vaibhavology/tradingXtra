"use client";
import { MarketBrief as MarketBriefType } from "@/lib/api";

export default function MarketBriefCard({ data }: { data: MarketBriefType }) {
  const biasColor =
    data.bias === "Bullish"
      ? "text-[var(--accent-green)]"
      : data.bias === "Bearish"
        ? "text-[var(--accent-red)]"
        : "text-[var(--accent-yellow)]";

  const behaviorIcon =
    data.behavior === "Trending" ? "📈" :
    data.behavior === "Volatile" ? "⚡" :
    data.behavior === "Range-bound" ? "↔️" : "❓";

  return (
    <div className="p-5">
      <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-widest mb-4 flex items-center gap-2">
        <span>📡</span> Market Brief
      </h3>

      {/* Bias + Behavior */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <span className="text-[11px] text-[var(--text-muted)] block mb-1">Bias</span>
          <span className={`text-sm font-semibold ${biasColor}`}>{data.bias}</span>
        </div>
        <div>
          <span className="text-[11px] text-[var(--text-muted)] block mb-1">Behavior</span>
          <span className="text-sm text-white">{behaviorIcon} {data.behavior}</span>
        </div>
      </div>

      {/* NIFTY Quick Stats */}
      {(data.nifty_return_5d !== undefined || data.vix) && (
        <div className="flex gap-3 mb-4 text-[11px]">
          {data.nifty_return_5d !== undefined && (
            <div className="bg-[var(--bg-primary)] rounded px-2 py-1">
              <span className="text-[var(--text-muted)]">NIFTY 5D </span>
              <span className={data.nifty_return_5d >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"}>
                {data.nifty_return_5d >= 0 ? "+" : ""}{data.nifty_return_5d?.toFixed(1)}%
              </span>
            </div>
          )}
          {data.vix && (
            <div className="bg-[var(--bg-primary)] rounded px-2 py-1">
              <span className="text-[var(--text-muted)]">VIX </span>
              <span className={data.vix > 20 ? "text-[var(--accent-red)]" : "text-[var(--accent-green)]"}>
                {data.vix.toFixed(1)}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Global Drivers */}
      {data.drivers?.global?.length > 0 && (
        <DriversSection label="🌍 Global" items={data.drivers.global} color="blue" />
      )}

      {/* India Drivers */}
      {data.drivers?.india?.length > 0 && (
        <DriversSection label="🇮🇳 India" items={data.drivers.india} color="blue" />
      )}

      {/* Sector Strength */}
      {data.sector_strength && (data.sector_strength.strong?.length > 0 || data.sector_strength.weak?.length > 0) && (
        <div className="mb-3">
          <span className="text-[11px] text-[var(--text-muted)] block mb-1.5">Sector Strength</span>
          <div className="flex flex-wrap gap-1.5">
            {data.sector_strength.strong?.map((s, i) => (
              <span key={`s-${i}`} className="text-[10px] bg-[var(--accent-green)]/10 text-[var(--accent-green)] px-2 py-0.5 rounded-full border border-[var(--accent-green)]/20">
                ▲ {s}
              </span>
            ))}
            {data.sector_strength.weak?.map((s, i) => (
              <span key={`w-${i}`} className="text-[10px] bg-[var(--accent-red)]/10 text-[var(--accent-red)] px-2 py-0.5 rounded-full border border-[var(--accent-red)]/20">
                ▼ {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Risk Alerts */}
      {data.risk_alerts?.length > 0 && (
        <div className="mb-3">
          <span className="text-[11px] text-[var(--text-muted)] block mb-1.5">Risk Alerts</span>
          {data.risk_alerts.map((r, i) => (
            <div key={i} className="text-[11px] text-[var(--accent-yellow)] bg-[var(--accent-yellow)]/5 px-2 py-1 rounded mb-1 border border-[var(--accent-yellow)]/10">
              ⚠ {r}
            </div>
          ))}
        </div>
      )}

      {/* Guidance */}
      {data.guidance?.length > 0 && (
        <div className="mb-3 pt-3 border-t border-[var(--border-default)]">
          <span className="text-[11px] text-[var(--text-muted)] block mb-1.5">Trading Guidance</span>
          <ul className="space-y-1">
            {data.guidance.map((g, i) => (
              <li key={i} className="text-[11px] text-[var(--text-secondary)] flex items-start gap-1.5">
                <span className="text-[var(--accent-blue)] mt-0.5">›</span>
                {g}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function DriversSection({ label, items, color }: { label: string; items: string[]; color: string }) {
  const cls = color === "blue" ? "bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] border-[var(--accent-blue)]/20" : "";
  return (
    <div className="mb-3">
      <span className="text-[11px] text-[var(--text-muted)] block mb-1.5">{label}</span>
      <div className="space-y-1">
        {items.map((d, i) => (
          <div key={i} className={`text-[10px] px-2 py-1 rounded border ${cls} truncate`} title={d}>
            {d}
          </div>
        ))}
      </div>
    </div>
  );
}
