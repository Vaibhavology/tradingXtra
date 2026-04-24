"use client";
import { InvestSmart } from "@/types";

interface Props {
  data: InvestSmart;
  systemDecisions?: Record<string, string>;
}

export default function InvestSmartCard({ data, systemDecisions }: Props) {
  if (!data) return null;

  const actionColor = (action: string) => {
    switch (action) {
      case "BUY": return "text-[var(--accent-green)] bg-[var(--accent-green)]/10 border-[var(--accent-green)]/20";
      case "AVOID": return "text-[var(--accent-red)] bg-[var(--accent-red)]/10 border-[var(--accent-red)]/20";
      default: return "text-[var(--accent-yellow)] bg-[var(--accent-yellow)]/10 border-[var(--accent-yellow)]/20";
    }
  };

  const actionIcon = (action: string) => {
    switch (action) {
      case "BUY": return "🟢";
      case "AVOID": return "🔴";
      default: return "🟡";
    }
  };

  const formatDate = (d: string) => {
    try {
      const date = new Date(d);
      const now = new Date();
      const diff = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
      if (diff < 1) return "Just now";
      if (diff < 24) return `${diff}h ago`;
      if (diff < 48) return "Yesterday";
      return `${Math.floor(diff / 24)}d ago`;
    } catch {
      return d;
    }
  };

  // Separate stocks by sentiment
  const buyStocks = data.stocks?.filter(s => s.action === "BUY") || [];
  const watchStocks = data.stocks?.filter(s => s.action === "WATCH") || [];
  const avoidStocks = data.stocks?.filter(s => s.action === "AVOID") || [];

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <span>📺</span> Invest Smart
        </h3>
        <span className="text-[10px] text-[var(--text-muted)] bg-[var(--bg-primary)] px-2 py-0.5 rounded">
          {data.source}
        </span>
      </div>

      {/* Video Info */}
      <div className="mb-4 pb-3 border-b border-[var(--border-default)]">
        <a
          href={data.link}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-[var(--accent-blue)] hover:underline line-clamp-2 leading-relaxed"
        >
          🎬 {data.title}
        </a>
        <span className="text-[10px] text-[var(--text-muted)] block mt-1">
          {formatDate(data.published)}
        </span>
      </div>

      {/* Video Takeaways */}
      {data.takeaways?.length > 0 && (
        <div className="mb-4">
          <span className="text-[11px] text-[var(--text-muted)] font-medium block mb-2">📋 Video Takeaways</span>
          <div className="space-y-1.5">
            {data.takeaways.map((t, i) => (
              <div key={i} className="text-[11px] text-[var(--text-secondary)] flex items-start gap-2 bg-[var(--bg-primary)] rounded px-2.5 py-1.5">
                <span className="text-[var(--accent-blue)] font-bold mt-0.5 shrink-0">{i + 1}.</span>
                <span className="leading-relaxed">{t}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Market Commentary */}
      {data.market_commentary && (
        <div className="mb-4 pb-3 border-b border-[var(--border-default)]">
          <span className="text-[11px] text-[var(--text-muted)] font-medium block mb-1.5">💬 Market Commentary</span>
          <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed bg-[var(--bg-primary)] rounded px-3 py-2 italic">
            &ldquo;{data.market_commentary}&rdquo;
          </p>
        </div>
      )}

      {/* Positive Stocks */}
      {buyStocks.length > 0 && (
        <StockSection
          label="🟢 Positive Outlook"
          stocks={buyStocks}
          actionColor={actionColor}
          actionIcon={actionIcon}
          systemDecisions={systemDecisions}
        />
      )}

      {/* Watch / Neutral Stocks */}
      {watchStocks.length > 0 && (
        <StockSection
          label="🟡 Neutral / Watch"
          stocks={watchStocks}
          actionColor={actionColor}
          actionIcon={actionIcon}
          systemDecisions={systemDecisions}
        />
      )}

      {/* Negative / Failed Setups */}
      {avoidStocks.length > 0 && (
        <StockSection
          label="🔴 Negative / Failed Setups"
          stocks={avoidStocks}
          actionColor={actionColor}
          actionIcon={actionIcon}
          systemDecisions={systemDecisions}
        />
      )}

      {/* No stocks extracted — show when Gemini analysis unavailable */}
      {data.stocks?.length === 0 && !data.market_commentary && (
        <div className="mb-3 p-3 bg-[var(--bg-primary)] rounded-lg border border-[var(--border-default)]">
          <div className="text-[11px] text-[var(--text-muted)] mb-2">
            ⚡ AI analysis temporarily unavailable — watch the video directly for stock insights
          </div>
          <a
            href={data.link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs bg-[var(--accent-blue)]/10 text-[var(--accent-blue)] rounded hover:bg-[var(--accent-blue)]/20 transition-colors"
          >
            ▶ Watch "{data.title?.slice(0, 50)}{data.title?.length > 50 ? '...' : ''}" on YouTube
          </a>
        </div>
      )}

      {/* Insights */}
      {data.insights?.length > 0 && (
        <div className="pt-3 border-t border-[var(--border-default)]">
          <span className="text-[11px] text-[var(--text-muted)] font-medium block mb-1.5">💡 Trading Insights</span>
          <ul className="space-y-1">
            {data.insights.map((insight, i) => (
              <li key={i} className="text-[11px] text-[var(--text-secondary)] flex items-start gap-1.5">
                <span className="text-[var(--accent-blue)] mt-0.5">•</span>
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* System Conflicts */}
      {systemDecisions && data.stocks?.length > 0 && (
        <ConflictSummary stocks={data.stocks} decisions={systemDecisions} />
      )}
    </div>
  );
}

/* ── Stock Section ────────────────────────────────────────────────── */

function StockSection({
  label,
  stocks,
  actionColor,
  actionIcon,
  systemDecisions,
}: {
  label: string;
  stocks: Array<{ symbol: string; action: string; reason: string; confidence: number; in_universe: boolean }>;
  actionColor: (a: string) => string;
  actionIcon: (a: string) => string;
  systemDecisions?: Record<string, string>;
}) {
  return (
    <div className="mb-3">
      <span className="text-[11px] text-[var(--text-muted)] font-medium block mb-2">{label}</span>
      <div className="space-y-1.5">
        {stocks.map((s, i) => {
          const sysDecision = systemDecisions?.[s.symbol];
          const hasConflict = sysDecision && (
            (s.action === "BUY" && sysDecision === "REJECT") ||
            (s.action === "AVOID" && sysDecision === "ACCEPT")
          );

          return (
            <div key={i} className="bg-[var(--bg-primary)] rounded px-2.5 py-2">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-white font-medium">{s.symbol}</span>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full border font-medium ${actionColor(s.action)}`}>
                    {actionIcon(s.action)} {s.action}
                  </span>
                  {!s.in_universe && (
                    <span className="text-[9px] text-[var(--text-muted)] bg-[var(--bg-card)] px-1 py-0.5 rounded">
                      External
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {/* Confidence */}
                  <div className="flex items-center gap-1">
                    <div className="w-10 h-1.5 bg-[var(--bg-card)] rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          s.action === "BUY" ? "bg-[var(--accent-green)]" :
                          s.action === "AVOID" ? "bg-[var(--accent-red)]" :
                          "bg-[var(--accent-yellow)]"
                        }`}
                        style={{ width: `${s.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-[9px] text-[var(--text-muted)]">{(s.confidence * 100).toFixed(0)}%</span>
                  </div>
                  {hasConflict && (
                    <span className="text-[9px] text-[var(--accent-red)] bg-[var(--accent-red)]/10 px-1.5 py-0.5 rounded border border-[var(--accent-red)]/20">
                      ⚠ CONFLICT
                    </span>
                  )}
                </div>
              </div>
              {/* Reason */}
              {s.reason && (
                <p className="text-[10px] text-[var(--text-muted)] leading-relaxed mt-0.5 pl-0.5">
                  {s.reason}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Conflict Summary ─────────────────────────────────────────────── */

function ConflictSummary({
  stocks,
  decisions,
}: {
  stocks: Array<{ symbol: string; action: string }>;
  decisions: Record<string, string>;
}) {
  const conflicts = stocks.filter(s => {
    const sys = decisions[s.symbol];
    return sys && (
      (s.action === "BUY" && sys === "REJECT") ||
      (s.action === "AVOID" && sys === "ACCEPT")
    );
  });

  if (conflicts.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-[var(--border-default)]">
      <span className="text-[10px] text-[var(--accent-red)] font-medium block mb-1.5">
        ⚠ System vs YouTube Conflicts ({conflicts.length})
      </span>
      {conflicts.map((c, i) => (
        <div key={i} className="text-[10px] text-[var(--text-muted)] flex items-center gap-2 py-0.5">
          <span className="font-mono text-white">{c.symbol}</span>
          <span className="text-[var(--accent-red)]">System → {decisions[c.symbol]}</span>
          <span className="text-[var(--text-muted)]">|</span>
          <span className="text-[var(--accent-yellow)]">YouTube → {c.action}</span>
        </div>
      ))}
      <p className="text-[9px] text-[var(--text-muted)] mt-1.5 italic">
        System risk-based decisions always take priority over YouTube suggestions
      </p>
    </div>
  );
}
