"use client";
import { InvestSmart, fetchAPI } from "@/lib/api";
import { useState, useEffect } from "react";
import { 
  RefreshCw, 
  Tv, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  PlayCircle, 
  ClipboardList, 
  MessageSquare, 
  Lightbulb, 
  AlertTriangle 
} from "lucide-react";

interface Props {
  data: InvestSmart | null;
  systemDecisions?: Record<string, string>;
}

export default function InvestSmartCard({ data, systemDecisions }: Props) {
  const [localData, setLocalData] = useState<InvestSmart | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (data) setLocalData(data);
  }, [data]);

  const handleRefresh = async () => {
    if (refreshing) return;
    setRefreshing(true);
    try {
      const res = await fetchAPI<{ status: string; data: InvestSmart }>("/invest-smart/refresh", {
        method: "POST"
      });
      if (res.status === "success" && res.data) {
        setLocalData(res.data);
      }
    } catch (e) {
      console.error("Failed to refresh invest smart:", e);
    } finally {
      setRefreshing(false);
    }
  };

  if (!localData) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-widest flex items-center gap-2">
            <Tv className="w-4 h-4 text-[var(--accent-blue)]" /> Invest Smart
            <button 
              onClick={handleRefresh}
              disabled={refreshing}
              className={`ml-2 p-1 rounded hover:bg-[var(--bg-primary)] transition-all ${refreshing ? "opacity-50 cursor-not-allowed" : "text-[var(--accent-blue)]"}`}
              title="Check for new video & analyze"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
            </button>
          </h3>
        </div>
        <div className="text-[11px] text-[var(--text-muted)] text-center py-8 bg-[var(--bg-primary)] rounded border border-dashed border-[var(--border-default)]">
          <p className="mb-2">No video analysis found.</p>
          <p>Click the refresh button to analyze the latest YouTube video.</p>
        </div>
      </div>
    );
  }

  const actionColor = (action: string) => {
    switch (action) {
      case "BUY": return "text-[var(--accent-green)] bg-[var(--accent-green)]/10 border-[var(--accent-green)]/20";
      case "AVOID": return "text-[var(--accent-red)] bg-[var(--accent-red)]/10 border-[var(--accent-red)]/20";
      default: return "text-[var(--accent-yellow)] bg-[var(--accent-yellow)]/10 border-[var(--accent-yellow)]/20";
    }
  };

  const actionIcon = (action: string) => {
    switch (action) {
      case "BUY": return <TrendingUp className="w-3 h-3" />;
      case "AVOID": return <TrendingDown className="w-3 h-3" />;
      default: return <Minus className="w-3 h-3" />;
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
  const buyStocks = localData.stocks?.filter(s => s.action === "BUY") || [];
  const watchStocks = localData.stocks?.filter(s => s.action === "WATCH") || [];
  const avoidStocks = localData.stocks?.filter(s => s.action === "AVOID") || [];

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-[var(--text-secondary)] uppercase tracking-widest flex items-center gap-2">
          <Tv className="w-4 h-4 text-[var(--accent-blue)]" /> Invest Smart
          <button 
            onClick={handleRefresh}
            disabled={refreshing}
            className={`ml-2 p-1 rounded hover:bg-[var(--bg-primary)] transition-all ${refreshing ? "opacity-50 cursor-not-allowed" : "text-[var(--accent-blue)]"}`}
            title="Check for new video & analyze"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
          </button>
        </h3>
        <span className="text-[10px] text-[var(--text-muted)] bg-[var(--bg-primary)] px-2 py-0.5 rounded">
          {localData.source}
        </span>
      </div>

      {/* Video Info */}
      <div className="mb-4 pb-3 border-b border-[var(--border-default)]">
        <a
          href={localData.link}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-[var(--accent-blue)] hover:underline line-clamp-2 leading-relaxed flex items-center gap-1.5"
        >
          <PlayCircle className="w-3.5 h-3.5 shrink-0" /> {localData.title}
        </a>
        <span className="text-[10px] text-[var(--text-muted)] block mt-1 ml-5">
          {formatDate(localData.published)}
        </span>
      </div>

      {/* Video Takeaways */}
      {localData.takeaways?.length > 0 && (
        <div className="mb-4">
          <span className="text-[11px] text-[var(--text-muted)] font-medium flex items-center gap-1.5 mb-2">
            <ClipboardList className="w-3.5 h-3.5" /> Video Takeaways
          </span>
          <div className="space-y-1.5">
            {localData.takeaways.map((t, i) => (
              <div key={i} className="text-[11px] text-[var(--text-secondary)] flex items-start gap-2 bg-[var(--bg-primary)] rounded px-2.5 py-1.5">
                <span className="text-[var(--accent-blue)] font-bold mt-0.5 shrink-0">{i + 1}.</span>
                <span className="leading-relaxed">{t}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Market Commentary */}
      {localData.market_commentary && (
        <div className="mb-4 pb-3 border-b border-[var(--border-default)]">
          <span className="text-[11px] text-[var(--text-muted)] font-medium flex items-center gap-1.5 mb-1.5">
            <MessageSquare className="w-3.5 h-3.5" /> Market Commentary
          </span>
          <p className="text-[11px] text-[var(--text-secondary)] leading-relaxed bg-[var(--bg-primary)] rounded px-3 py-2 italic">
            &ldquo;{localData.market_commentary}&rdquo;
          </p>
        </div>
      )}

      {/* Positive Stocks */}
      {buyStocks.length > 0 && (
        <StockSection
          label={
            <span className="flex items-center gap-1.5 text-[var(--accent-green)]">
              <TrendingUp className="w-3.5 h-3.5" /> Positive Outlook
            </span>
          }
          stocks={buyStocks}
          actionColor={actionColor}
          actionIcon={actionIcon}
          systemDecisions={systemDecisions}
        />
      )}

      {/* Watch / Neutral Stocks */}
      {watchStocks.length > 0 && (
        <StockSection
          label={
            <span className="flex items-center gap-1.5 text-[var(--accent-yellow)]">
              <Minus className="w-3.5 h-3.5" /> Neutral / Watch
            </span>
          }
          stocks={watchStocks}
          actionColor={actionColor}
          actionIcon={actionIcon}
          systemDecisions={systemDecisions}
        />
      )}

      {/* Negative / Failed Setups */}
      {avoidStocks.length > 0 && (
        <StockSection
          label={
            <span className="flex items-center gap-1.5 text-[var(--accent-red)]">
              <TrendingDown className="w-3.5 h-3.5" /> Negative / Failed Setups
            </span>
          }
          stocks={avoidStocks}
          actionColor={actionColor}
          actionIcon={actionIcon}
          systemDecisions={systemDecisions}
        />
      )}

      {/* No stocks extracted */}
      {localData.stocks?.length === 0 && (
        <div className="text-[11px] text-[var(--text-muted)] text-center py-3 bg-[var(--bg-primary)] rounded mb-3">
          No specific stocks extracted — watch the video for details
        </div>
      )}

      {/* Insights */}
      {localData.insights?.length > 0 && (
        <div className="pt-3 border-t border-[var(--border-default)]">
          <span className="text-[11px] text-[var(--text-muted)] font-medium flex items-center gap-1.5 mb-1.5">
            <Lightbulb className="w-3.5 h-3.5" /> Trading Insights
          </span>
          <ul className="space-y-1">
            {localData.insights.map((insight, i) => (
              <li key={i} className="text-[11px] text-[var(--text-secondary)] flex items-start gap-1.5">
                <span className="text-[var(--accent-blue)] mt-0.5">•</span>
                {insight}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* System Conflicts */}
      {systemDecisions && localData.stocks?.length > 0 && (
        <ConflictSummary stocks={localData.stocks} decisions={systemDecisions} />
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
  label: React.ReactNode;
  stocks: Array<{ symbol: string; action: string; reason: string; confidence: number; in_universe: boolean }>;
  actionColor: (a: string) => string;
  actionIcon: (a: string) => React.ReactNode;
  systemDecisions?: Record<string, string>;
}) {
  return (
    <div className="mb-3">
      <div className="text-[11px] text-[var(--text-muted)] font-medium block mb-2">{label}</div>
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
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-full border font-medium flex items-center gap-1 ${actionColor(s.action)}`}>
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
                    <span className="text-[9px] text-[var(--accent-red)] bg-[var(--accent-red)]/10 px-1.5 py-0.5 rounded border border-[var(--accent-red)]/20 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> CONFLICT
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
      <span className="text-[10px] text-[var(--accent-red)] font-medium flex items-center gap-1.5 mb-1.5">
        <AlertTriangle className="w-3.5 h-3.5" /> System vs YouTube Conflicts ({conflicts.length})
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
