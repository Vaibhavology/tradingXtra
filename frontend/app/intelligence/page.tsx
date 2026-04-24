"use client";

import { useEffect, useState } from "react";
import { getMarketBrief, MarketBrief as MarketBriefType } from "@/lib/api";

export default function IntelligencePage() {
  const [brief, setBrief] = useState<MarketBriefType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getMarketBrief();
        setBrief(data);
      } catch (err: any) {
        setError(err.message || "Failed to load market intelligence.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center h-96">
        <div className="animate-pulse flex flex-col items-center">
          <span className="text-4xl mb-4">📡</span>
          <span className="text-[var(--text-muted)] font-mono uppercase tracking-widest text-sm">Intercepting Market Data...</span>
        </div>
      </div>
    );
  }

  if (error || !brief) {
    return (
      <div className="p-6 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded text-[var(--accent-red)] font-mono text-sm max-w-2xl mx-auto mt-10">
        [ERROR]: {error || "No data returned from command center."}
      </div>
    );
  }

  return (
    <div className="max-w-[1200px] mx-auto space-y-8 pb-12">
      {/* HEADER STRIP */}
      <div className="terminal-card rounded-xl p-8 border border-[var(--border-default)] shadow-xl relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="absolute -top-20 -right-20 w-64 h-64 bg-[var(--accent-blue)]/5 rounded-full blur-[80px]" />
        
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl">📡</span>
            <h1 className="text-3xl font-black text-white tracking-tight uppercase">Market Intelligence</h1>
          </div>
          <p className="text-[var(--text-muted)] text-sm max-w-xl leading-relaxed">
            Advanced real-time market regime detection, global sentiment analysis, and risk assessment parameters.
          </p>
        </div>

        <div className="flex items-center gap-6 bg-[var(--bg-secondary)]/50 p-4 rounded-lg border border-[var(--border-default)]">
          <div className="text-center">
            <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold tracking-wider mb-1">Market Bias</div>
            <div className={`text-xl font-black uppercase ${
              brief.bias === "Bullish" ? "text-[var(--accent-green)]" :
              brief.bias === "Bearish" ? "text-[var(--accent-red)]" : "text-[var(--accent-yellow)]"
            }`}>
              {brief.bias}
            </div>
          </div>
          <div className="w-px h-10 bg-[var(--border-default)]" />
          <div className="text-center">
            <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold tracking-wider mb-1">Behavior</div>
            <div className="text-xl font-black text-white uppercase">{brief.behavior}</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: News Feeds & Drivers */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Global News */}
          <div className="terminal-card rounded-xl p-6 border border-[var(--border-default)] shadow-lg">
            <div className="flex items-center justify-between mb-6 border-b border-[var(--border-default)] pb-4">
              <h2 className="text-lg font-bold text-white uppercase tracking-widest flex items-center gap-2">
                <span>🌍</span> Global Market Drivers
              </h2>
              <span className="text-[10px] font-mono bg-[var(--bg-secondary)] px-2 py-1 rounded text-[var(--text-muted)] border border-[var(--border-default)]">
                MACRO SENTIMENT
              </span>
            </div>
            
            <div className="space-y-4">
              {brief.drivers?.global?.length > 0 ? (
                brief.drivers.global.map((news, idx) => (
                  <div key={idx} className="group p-4 bg-[var(--bg-secondary)]/30 hover:bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-default)]/50 transition-colors">
                    <p className="text-sm text-[var(--text-primary)] leading-relaxed">{news}</p>
                  </div>
                ))
              ) : (
                <div className="text-sm text-[var(--text-muted)] italic">No significant global drivers detected.</div>
              )}
            </div>
          </div>

          {/* India News */}
          <div className="terminal-card rounded-xl p-6 border border-[var(--border-default)] shadow-lg">
            <div className="flex items-center justify-between mb-6 border-b border-[var(--border-default)] pb-4">
              <h2 className="text-lg font-bold text-white uppercase tracking-widest flex items-center gap-2">
                <span>🇮🇳</span> Domestic Market Drivers
              </h2>
              <span className="text-[10px] font-mono bg-[var(--bg-secondary)] px-2 py-1 rounded text-[var(--text-muted)] border border-[var(--border-default)]">
                NSE CATALYSTS
              </span>
            </div>
            
            <div className="space-y-4">
              {brief.drivers?.india?.length > 0 ? (
                brief.drivers.india.map((news, idx) => (
                  <div key={idx} className="group p-4 bg-[var(--bg-secondary)]/30 hover:bg-[var(--bg-secondary)] rounded-lg border border-[var(--border-default)]/50 transition-colors">
                    <p className="text-sm text-[var(--text-primary)] leading-relaxed">{news}</p>
                  </div>
                ))
              ) : (
                <div className="text-sm text-[var(--text-muted)] italic">No significant domestic drivers detected.</div>
              )}
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN: Quantitative & Risk */}
        <div className="space-y-6 flex flex-col">
          
          {/* Quantitative Indicators */}
          <div className="terminal-card rounded-xl p-6 border border-[var(--border-default)] shadow-lg">
            <h2 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-widest mb-6 flex items-center gap-2">
              <span>📊</span> Quantitative Data
            </h2>
            
            <div className="space-y-5">
              <div>
                <div className="flex justify-between items-end mb-1">
                  <span className="text-xs uppercase text-[var(--text-muted)] font-bold">NIFTY 5D Trend</span>
                  <span className={`text-lg font-mono font-bold ${
                    brief.nifty_return_5d >= 0 ? "text-[var(--accent-green)]" : "text-[var(--accent-red)]"
                  }`}>
                    {brief.nifty_return_5d >= 0 ? "+" : ""}{brief.nifty_return_5d?.toFixed(2)}%
                  </span>
                </div>
                <div className="h-1.5 w-full bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                  <div className={`h-full ${brief.nifty_return_5d >= 0 ? 'bg-[var(--accent-green)]' : 'bg-[var(--accent-red)]'}`} style={{ width: `${Math.min(abs(brief.nifty_return_5d) * 10, 100)}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between items-end mb-1">
                  <span className="text-xs uppercase text-[var(--text-muted)] font-bold">INDIA VIX (Volatility)</span>
                  <span className={`text-lg font-mono font-bold ${
                    brief.vix && brief.vix > 20 ? "text-[var(--accent-red)]" : "text-[var(--accent-green)]"
                  }`}>
                    {brief.vix?.toFixed(2) || "N/A"}
                  </span>
                </div>
                <div className="h-1.5 w-full bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                  <div className={`h-full ${brief.vix && brief.vix > 20 ? 'bg-[var(--accent-red)]' : 'bg-[var(--accent-green)]'}`} style={{ width: `${Math.min((brief.vix || 0) * 3, 100)}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Actionable Guidance */}
          <div className="terminal-card rounded-xl p-6 border border-[var(--border-default)] shadow-lg bg-[var(--bg-secondary)]/10">
            <h2 className="text-sm font-bold text-[var(--accent-blue)] uppercase tracking-widest mb-4 flex items-center gap-2">
              <span>🎯</span> Tactical Playbook
            </h2>
            
            <ul className="space-y-3">
              {brief.guidance?.map((g, i) => (
                <li key={i} className="text-sm text-white flex items-start gap-2 bg-[var(--bg-card)] p-3 rounded border border-[var(--border-default)] shadow-sm">
                  <span className="text-[var(--accent-blue)] mt-0.5">›</span>
                  <span className="leading-snug">{g}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Risk Terminal */}
          <div className="terminal-card rounded-xl p-6 border border-[var(--accent-red)]/30 bg-[var(--accent-red)]/5 shadow-[0_0_15px_rgba(255,51,102,0.05)]">
            <h2 className="text-sm font-bold text-[var(--accent-red)] uppercase tracking-widest mb-4 flex items-center gap-2">
              <span>⚠</span> Critical Risk Alerts
            </h2>
            
            <div className="space-y-3">
              {brief.risk_alerts?.length > 0 ? (
                brief.risk_alerts.map((alert, idx) => (
                  <div key={idx} className="text-xs text-[var(--text-primary)] p-3 border-l-2 border-[var(--accent-red)] bg-[var(--bg-card)]/80 leading-relaxed">
                    {alert}
                  </div>
                ))
              ) : (
                <div className="text-xs text-[var(--accent-green)] p-3 border-l-2 border-[var(--accent-green)] bg-[var(--bg-card)]/80">
                  No critical risk events detected. Standard risk management applies.
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// Math.abs helper for the UI
function abs(num: number | undefined | null): number {
  if (num === null || num === undefined) return 0;
  return Math.abs(num);
}
