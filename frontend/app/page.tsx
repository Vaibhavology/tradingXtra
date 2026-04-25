"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import {
  getScan, getMarketBrief, getPortfolio, getPerformance, refreshInvestSmart, wakeBackend,
  ScanResult, MarketBrief as MarketBriefType, PortfolioState, PerformanceData, TradeDecision,
} from "@/lib/api";
import { Activity, AlertTriangle, Monitor, Globe, MapPin, RefreshCw } from "lucide-react";
import PickCard from "@/components/PickCard";
import PortfolioCard from "@/components/PortfolioCard";
import PerformanceCard from "@/components/PerformanceCard";
import ChartAnalyzerCard from "@/components/ChartAnalyzerCard";

export default function Dashboard() {
  const [scan, setScan] = useState<ScanResult | null>(null);
  const [brief, setBrief] = useState<MarketBriefType | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioState | null>(null);
  const [perf, setPerf] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanLoading, setScanLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAlertModalOpen, setIsAlertModalOpen] = useState(false);
  const [refreshingInvestSmart, setRefreshingInvestSmart] = useState(false);

  const handleRefreshInvestSmart = async () => {
    if (refreshingInvestSmart) return;
    setRefreshingInvestSmart(true);
    try {
      const res = await refreshInvestSmart();
      if (res.status === "success" && res.data) {
        setBrief(prev => prev ? { ...prev, invest_smart: res.data } : prev);
      }
    } catch (e) {
      console.error("Failed to refresh invest smart:", e);
    } finally {
      setRefreshingInvestSmart(false);
    }
  };

  useEffect(() => {
    // Wake up Render backend immediately (fights cold start)
    wakeBackend();

    // Progressive loading: show data as each API resolves
    // Fast APIs first (market-brief, portfolio, performance)
    // Slow API last (scan — evaluates 35 stocks)
    async function loadFast() {
      try {
        const [b, p, pf] = await Promise.allSettled([
          getMarketBrief(), getPortfolio(), getPerformance(),
        ]);
        if (b.status === "fulfilled") setBrief(b.value);
        if (p.status === "fulfilled") setPortfolio(p.value);
        if (pf.status === "fulfilled") setPerf(pf.value);
      } catch (e) {
        console.error("Fast load error:", e);
      } finally {
        setLoading(false); // Show UI as soon as fast data is ready
      }
    }

    async function loadScan() {
      try {
        const s = await getScan();
        setScan(s);
      } catch (e) {
        console.error("Scan load error:", e);
      } finally {
        setScanLoading(false);
      }
    }

    loadFast();
    loadScan();

    const interval = setInterval(() => {
      loadFast();
      loadScan();
    }, 90_000); // Refresh every 90s instead of 60s to reduce load
    return () => clearInterval(interval);
  }, []);

  if (loading) return <LoadingState />;
  if (error) return <ErrorState message={error} />;

  // Split results by decision
  const results = scan?.results || [];
  const acceptedPicks = results.filter(r => r.decision === "ACCEPT");
  const rejectedPicks = results.filter(r => r.decision !== "ACCEPT");

  const bias = brief?.bias || "Neutral";
  const behavior = brief?.behavior || "Unknown";
  const confidence = brief ? Math.abs(brief.scores.bias_score * 100).toFixed(0) : "0";

  return (
    <div className="space-y-12 max-w-[1600px] mx-auto pb-16 animate-fade-in">
      
      {/* 1. MARKET STATE (FIRST THING USER SEES) */}
      <div className="relative overflow-hidden rounded-3xl border border-[var(--border-default)] bg-[var(--bg-card)] shadow-2xl p-8 lg:p-12 hover:shadow-3xl transition-shadow duration-500 group">
        <div className={`absolute top-0 right-0 w-[600px] h-[600px] rounded-full blur-[120px] opacity-10 md:opacity-20 pointer-events-none transition-colors duration-1000 ${
            bias === 'Bullish' ? 'bg-[var(--accent-green)]' : bias === 'Bearish' ? 'bg-[var(--accent-red)]' : 'bg-[var(--text-muted)]'
        }`} />
        
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-end gap-8">
           <div>
              <div className="flex items-center gap-3 mb-4">
                 <span className="relative flex h-3 w-3">
                   <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[var(--accent-green-light)] opacity-75"></span>
                   <span className="relative inline-flex rounded-full h-3 w-3 bg-[var(--accent-green)]"></span>
                 </span>
                 <p className="text-[var(--text-muted)] font-mono text-xs uppercase tracking-widest font-bold">Market State</p>
              </div>
              
              <h1 className="text-5xl md:text-7xl font-black text-white tracking-tighter mb-4 flex items-baseline gap-4">
                 {bias} <span className="opacity-40 text-3xl md:text-5xl font-light">Day</span>
              </h1>
              
              <div className="text-xl md:text-2xl text-[var(--text-secondary)] font-light leading-relaxed max-w-2xl">
                 Market behavior is <strong className="text-white font-medium">{behavior}</strong> with <strong className="text-white font-mono">{confidence}%</strong> directional confidence.
              </div>
           </div>
           
           <div className="flex flex-col gap-3 shrink-0">
               <div className="flex flex-col gap-2 bg-[var(--bg-primary)]/80 backdrop-blur-md p-4 rounded-xl border border-[var(--border-default)] shadow-lg">
                   <span className="text-[10px] text-[var(--text-muted)] uppercase tracking-widest font-bold">System Status</span>
                   <div className="flex gap-3">
                       <div className="flex flex-col">
                           <span className="text-lg font-mono font-bold text-white">{scan?.total || 0}</span>
                           <span className="text-[10px] text-[var(--text-muted)] uppercase">Scanned</span>
                       </div>
                       <div className="w-px bg-[var(--border-default)]"></div>
                       <div className="flex flex-col">
                           <span className="text-lg font-mono font-bold text-[var(--accent-green)]">{scan?.accepted || 0}</span>
                           <span className="text-[10px] text-[var(--accent-green)]/70 uppercase">Picks</span>
                       </div>
                   </div>
               </div>
           </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
        
        {/* 2. ACTIONABLE OPPORTUNITIES (Medium-Big) */}
        <div className="lg:col-span-8 space-y-6">
          <div className="flex items-end justify-between border-b border-[var(--border-default)]/50 pb-4">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight">Actionable Opportunities</h2>
              <p className="text-sm font-mono text-[var(--text-muted)] mt-1">SYSTEM PICKS & REASONING</p>
            </div>
          </div>
          
          {scanLoading ? (
            <div className="terminal-card rounded-2xl p-16 text-center flex flex-col items-center justify-center border-dashed border-2 border-[var(--border-default)] bg-[var(--bg-card)]/50">
              <Activity className="w-12 h-12 mb-4 opacity-60 text-[var(--accent-blue)] animate-pulse" />
              <p className="text-xl text-[var(--text-primary)] font-medium tracking-tight">Scanning 35 Stocks...</p>
              <p className="text-sm text-[var(--text-muted)] mt-2">Evaluating momentum, patterns & risk for the full universe</p>
              <div className="mt-4 w-48 h-1 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                <div className="h-full bg-[var(--accent-blue)] rounded-full animate-pulse" style={{width: '60%'}} />
              </div>
            </div>
          ) : acceptedPicks.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {acceptedPicks.map(pick => (
                <div key={pick.symbol} className="hover:-translate-y-1 transition-transform duration-300">
                  <PickCard pick={pick} />
                </div>
              ))}
            </div>
          ) : (
            <div className="terminal-card rounded-2xl p-16 text-center flex flex-col items-center justify-center border-dashed border-2 border-[var(--border-default)] bg-[var(--bg-card)]/50">
              <Activity className="w-12 h-12 mb-4 opacity-40 text-[var(--text-primary)]" />
              <p className="text-xl text-[var(--text-primary)] font-medium tracking-tight">No Opportunities Today</p>
              <p className="text-sm text-[var(--text-muted)] mt-2">No stocks passed the EV gates. Check back later.</p>
            </div>
          )}

          {rejectedPicks.length > 0 && (
            <div className="mt-8 pt-6 opacity-60 hover:opacity-100 transition-opacity duration-300">
              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-4 flex items-center gap-2">
                <span>Filtered Out</span>
                <span className="bg-[var(--bg-card)] px-2 py-0.5 rounded text-[10px] border border-[var(--border-default)] font-mono">
                  {rejectedPicks.length}
                </span>
              </h3>
              <div className="bg-[var(--bg-secondary)]/50 border border-[var(--border-default)] rounded-xl overflow-hidden backdrop-blur-sm">
                <table className="w-full text-[12px]">
                  <tbody>
                    {rejectedPicks.slice(0, 5).map(r => (
                      <tr key={r.symbol} className="border-b border-[var(--border-default)]/30 hover:bg-[var(--bg-card)] transition-colors">
                        <td className="p-3 font-mono font-medium text-[var(--text-secondary)] w-24">{r.symbol}</td>
                        <td className="p-3 text-[var(--text-muted)] truncate max-w-[200px]">{r.rejection_reason || "Failed EV gates"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* 3. RISK CONTEXT (Medium-Small) */}
        <div className="lg:col-span-4 space-y-6">
          <div className="flex items-end justify-between border-b border-[var(--border-default)]/50 pb-4">
            <div>
              <h2 className="text-2xl font-bold text-[var(--text-secondary)] tracking-tight">Risk Context</h2>
              <p className="text-sm font-mono text-[var(--text-muted)] mt-1">WHAT CAN GO WRONG</p>
            </div>
          </div>

          <div className="flex flex-col gap-5">
             {/* Risk Alerts (Clickable) */}
             <div 
                onClick={() => setIsAlertModalOpen(true)}
                className="bg-red-500/5 border border-red-500/20 rounded-2xl p-6 hover:-translate-y-1 transition-transform duration-300 shadow-xl relative overflow-hidden cursor-pointer group"
             >
                <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-3xl group-hover:bg-red-500/20 transition-colors" />
                <div className="flex justify-between items-start relative z-10 mb-4">
                  <h3 className="text-xs uppercase tracking-widest font-black text-red-400 flex items-center gap-2">
                     <AlertTriangle className="w-5 h-5" /> Market Alerts
                  </h3>
                  <span className="text-[10px] bg-red-500/20 text-red-400 px-2 py-1 rounded font-bold uppercase tracking-widest">Expand</span>
                </div>
                <ul className="space-y-4 relative z-10">
                   {brief?.risk_alerts?.map((alert, i) => (
                      <li key={i} className="text-sm text-[var(--text-primary)] leading-relaxed border-l-2 border-red-500/40 pl-4 font-medium line-clamp-2">
                         {alert}
                      </li>
                   ))}
                   {(!brief?.risk_alerts || brief.risk_alerts.length === 0) && (
                      <li className="text-sm text-[var(--text-muted)] italic">No active critical alerts.</li>
                   )}
                </ul>
             </div>

             {/* Volatility & Sector Weakness */}
             <div className="grid grid-cols-2 gap-5">
                <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl p-6 shadow-xl hover:-translate-y-1 transition-transform duration-300">
                   <p className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] font-bold mb-2">Volatility</p>
                   <p className="text-4xl font-black font-mono text-white tracking-tighter">{brief?.vix ? brief.vix.toFixed(1) : "--"}</p>
                   <p className="text-[10px] text-[var(--text-muted)] mt-2 font-mono">INDIA VIX</p>
                </div>
                <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl p-6 shadow-xl hover:-translate-y-1 transition-transform duration-300">
                   <p className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] font-bold mb-2">Weak Sectors</p>
                   <div className="flex flex-col gap-1.5 mt-3">
                      {brief?.sector_strength?.weak?.slice(0,2).map(s => (
                         <span key={s} className="text-xs text-[var(--accent-red)] font-semibold truncate bg-red-500/10 px-2 py-1 rounded w-fit">{s}</span>
                      ))}
                      {(!brief?.sector_strength?.weak || brief.sector_strength.weak.length === 0) && (
                         <span className="text-xs text-[var(--text-muted)]">None detected</span>
                      )}
                   </div>
                </div>
             </div>
             
             {/* Tools / Integrations */}
             <div className="mt-2 hover:-translate-y-1 transition-transform duration-300">
                <ChartAnalyzerCard />
             </div>
          </div>
        </div>
      </div>

      {/* 4. INVEST SMART (HUMAN INTELLIGENCE) */}
      {brief?.invest_smart && (
         <div className="mt-16 pt-8 border-t border-[var(--border-default)]/30">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
               <div>
                  <div className="flex items-center gap-3">
                     <Monitor className="w-8 h-8 text-[var(--accent-blue)] drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]" />
                     <h2 className="text-2xl md:text-3xl font-black text-white tracking-tight">Invest Smart</h2>
                  </div>
                  <p className="text-xs font-mono text-[var(--accent-blue)] uppercase tracking-widest mt-2 ml-11 font-bold">Expert Market Thinking Layer</p>
               </div>
               
               <button 
                 onClick={handleRefreshInvestSmart}
                 disabled={refreshingInvestSmart}
                 className={`flex items-center gap-2 px-4 py-2 rounded-xl border border-[var(--border-default)] bg-[var(--bg-card)] hover:bg-[var(--bg-primary)] hover:border-[var(--accent-blue)]/50 transition-all text-sm font-medium text-[var(--text-secondary)] ${refreshingInvestSmart ? "opacity-50 cursor-not-allowed" : ""}`}
                 title="Fetch and analyze latest YouTube video"
               >
                 <RefreshCw className={`w-4 h-4 ${refreshingInvestSmart ? "animate-spin text-[var(--accent-blue)]" : ""}`} />
                 {refreshingInvestSmart ? "Analyzing..." : "Refresh Video"}
               </button>
            </div>
            
            <div className="group relative bg-[var(--bg-card)] border border-[var(--border-default)] hover:border-[var(--accent-blue)]/40 transition-colors duration-500 rounded-3xl overflow-hidden shadow-2xl p-8 lg:p-10">
               <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent-blue)]/5 via-transparent to-transparent opacity-50 group-hover:opacity-100 transition-opacity duration-500" />
               
               <div className="relative z-10 flex flex-col xl:flex-row gap-10">
                  {/* Left: Video Context */}
                  <div className="xl:w-1/3 flex flex-col gap-6">
                     <a href={brief.invest_smart.link} target="_blank" rel="noreferrer" className="inline-block hover:-translate-y-0.5 transition-transform">
                       <h3 className="text-2xl md:text-3xl font-bold text-white hover:text-[var(--accent-blue)] transition-colors leading-tight">
                         {brief.invest_smart.title}
                       </h3>
                     </a>
                     <div className="bg-[var(--bg-primary)]/50 backdrop-blur-sm p-5 rounded-2xl border border-[var(--border-default)]/50">
                       <p className="text-sm text-[var(--text-secondary)] leading-relaxed italic">
                         &quot;{brief.invest_smart.market_commentary}&quot;
                       </p>
                     </div>
                  </div>

                  {/* Right: Extracted Intelligence Grid */}
                  <div className="xl:w-2/3 grid grid-cols-1 md:grid-cols-2 gap-8">
                     
                     <div className="space-y-8">
                        {/* Strategy Insight */}
                        <div>
                           <h4 className="text-[10px] font-black uppercase tracking-widest text-[var(--accent-blue)] mb-4 flex items-center gap-2">
                              <span className="w-4 h-px bg-[var(--accent-blue)]"></span> Strategy Insight
                           </h4>
                           <ul className="space-y-4">
                              {brief.invest_smart.takeaways && brief.invest_smart.takeaways.length > 0 ? (
                                 brief.invest_smart.takeaways.slice(0,3).map((t, i) => (
                                    <li key={i} className="text-sm text-[var(--text-primary)] flex items-start gap-3">
                                       <span className="text-[var(--accent-blue)] mt-0.5 opacity-60">↳</span>
                                       <span className="leading-relaxed font-medium">{t}</span>
                                    </li>
                                 ))
                              ) : (
                                 <li className="text-sm text-[var(--text-muted)] italic">No specific strategy takeaways extracted.</li>
                              )}
                           </ul>
                        </div>

                        {/* Market Narrative */}
                        <div>
                           <h4 className="text-[10px] font-black uppercase tracking-widest text-[var(--accent-purple)] mb-4 flex items-center gap-2">
                              <span className="w-4 h-px bg-[var(--accent-purple)]"></span> Market Narrative
                           </h4>
                           <ul className="space-y-4">
                              {brief.invest_smart.insights && brief.invest_smart.insights.length > 0 ? (
                                 brief.invest_smart.insights.slice(0,3).map((t, i) => (
                                    <li key={i} className="text-sm text-[var(--text-primary)] flex items-start gap-3">
                                       <span className="text-[var(--accent-purple)] mt-0.5 opacity-60">↳</span>
                                       <span className="leading-relaxed font-medium">{t}</span>
                                    </li>
                                 ))
                              ) : (
                                 <li className="text-sm text-[var(--text-muted)] italic">No market narrative insights available.</li>
                              )}
                           </ul>
                        </div>
                     </div>

                     {/* Stocks Discussed */}
                     {/* Stocks Discussed */}
                     <div className="bg-[var(--bg-primary)]/30 rounded-2xl p-6 border border-[var(--border-default)]/30">
                        <h4 className="text-[10px] font-black uppercase tracking-widest text-[var(--accent-green)] mb-5 flex items-center gap-2">
                           <span className="w-4 h-px bg-[var(--accent-green)]"></span> Stocks Discussed
                        </h4>
                        <div className="flex flex-col gap-3 h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                           {brief.invest_smart.stocks && brief.invest_smart.stocks.length > 0 ? (
                              brief.invest_smart.stocks.map((s, i) => (
                                 <div key={i} className="flex flex-col bg-[var(--bg-card)] p-4 rounded-xl border border-[var(--border-default)] shadow-sm hover:shadow-md transition-shadow group/stock">
                                    <div className="flex justify-between items-center mb-2">
                                       <span className="font-mono text-white font-bold text-sm group-hover/stock:text-[var(--accent-blue)] transition-colors">{s.symbol}</span>
                                       <span className={`text-[9px] px-2.5 py-1 rounded-md font-black tracking-widest uppercase ${
                                          s.action === 'BUY' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                                          s.action === 'AVOID' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                                          'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                                       }`}>{s.action}</span>
                                    </div>
                                    <p className="text-xs text-[var(--text-muted)] leading-relaxed">{s.reason}</p>
                                 </div>
                              ))
                           ) : (
                              <div className="flex flex-col items-center justify-center h-full text-center p-4">
                                 <Monitor className="w-8 h-8 text-[var(--text-muted)] mb-3 opacity-50" />
                                 <p className="text-sm text-[var(--text-secondary)] font-medium">No specific stocks highlighted</p>
                                 <p className="text-xs text-[var(--text-muted)] mt-1">Watch the video for broader market analysis</p>
                              </div>
                           )}
                        </div>
                     </div>

                  </div>
               </div>
            </div>
         </div>
      )}

      {/* 5. SYSTEM METRICS (Footer) */}
      {(portfolio || perf) && (
        <div className="mt-16 pt-8 border-t border-[var(--border-default)]/30 flex flex-col lg:flex-row gap-6 opacity-60 hover:opacity-100 transition-opacity duration-300">
          {portfolio && (
            <div className="lg:w-1/2 terminal-card rounded-2xl overflow-hidden shadow-lg p-1">
              <PortfolioCard data={portfolio} />
            </div>
          )}
          {perf && (
            <div className="lg:w-1/2 terminal-card rounded-2xl overflow-hidden shadow-lg p-1">
              <PerformanceCard data={perf} />
            </div>
          )}
        </div>
      )}

      {/* Expanded Market Context Modal */}
      {isAlertModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in" onClick={() => setIsAlertModalOpen(false)}>
          <div 
            className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col relative"
            onClick={e => e.stopPropagation()}
          >
            <div className="p-6 border-b border-[var(--border-default)] flex justify-between items-center bg-[var(--bg-primary)]">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-6 h-6 text-white" />
                <h2 className="text-xl font-bold text-white tracking-tight">Expanded Market Context</h2>
              </div>
              <button 
                onClick={() => setIsAlertModalOpen(false)}
                className="text-[var(--text-muted)] hover:text-white p-2 rounded-lg hover:bg-[var(--bg-secondary)] transition-colors"
              >
                ✕
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto custom-scrollbar flex flex-col gap-8">
              
              {/* Macro Indicators Row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-[var(--bg-primary)] border border-[var(--border-default)] rounded-xl p-4">
                  <p className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] font-bold mb-1">India VIX</p>
                  <p className="text-2xl font-black font-mono text-white">{brief?.vix ? brief.vix.toFixed(2) : "--"}</p>
                </div>
                <div className="bg-[var(--bg-primary)] border border-[var(--border-default)] rounded-xl p-4">
                  <p className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] font-bold mb-1">USD/INR</p>
                  <div className="flex items-end gap-2">
                    <p className="text-2xl font-black font-mono text-white">{brief?.usd_inr?.price ? brief.usd_inr.price.toFixed(2) : "--"}</p>
                    <p className={`text-xs font-bold mb-1 ${brief?.usd_inr?.change_pct && brief.usd_inr.change_pct > 0 ? 'text-red-400' : 'text-green-400'}`}>
                      {brief?.usd_inr?.change_pct && brief.usd_inr.change_pct > 0 ? '+' : ''}{brief?.usd_inr?.change_pct?.toFixed(2)}%
                    </p>
                  </div>
                </div>
                <div className="bg-[var(--bg-primary)] border border-[var(--border-default)] rounded-xl p-4">
                  <p className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] font-bold mb-1">NIFTY 5D</p>
                  <p className={`text-2xl font-black font-mono ${brief?.nifty_return_5d && brief.nifty_return_5d >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {brief?.nifty_return_5d && brief.nifty_return_5d > 0 ? '+' : ''}{brief?.nifty_return_5d?.toFixed(2)}%
                  </p>
                </div>
                <div className="bg-[var(--bg-primary)] border border-[var(--border-default)] rounded-xl p-4">
                  <p className="text-[10px] uppercase tracking-widest text-[var(--text-muted)] font-bold mb-1">Market Bias</p>
                  <p className={`text-2xl font-black font-mono uppercase ${bias === 'Bullish' ? 'text-green-400' : bias === 'Bearish' ? 'text-red-400' : 'text-yellow-400'}`}>
                    {bias}
                  </p>
                </div>
              </div>

              {/* News Grids */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                
                {/* Global News */}
                <div>
                  <h3 className="text-xs font-black uppercase tracking-widest text-[var(--accent-blue)] mb-4 flex items-center gap-2">
                    <Globe className="w-5 h-5" /> Global Market Drivers
                  </h3>
                  <ul className="space-y-3">
                    {brief?.drivers?.global?.map((news, i) => (
                      <li key={i} className="bg-[var(--bg-primary)] border border-[var(--border-default)] p-4 rounded-xl text-sm text-[var(--text-primary)] leading-relaxed">
                        {news}
                      </li>
                    ))}
                    {(!brief?.drivers?.global || brief.drivers.global.length === 0) && (
                      <li className="text-sm text-[var(--text-muted)] italic">No critical global news.</li>
                    )}
                  </ul>
                </div>

                {/* India News */}
                <div>
                  <h3 className="text-xs font-black uppercase tracking-widest text-orange-400 mb-4 flex items-center gap-2">
                    <MapPin className="w-5 h-5" /> Domestic Catalysts
                  </h3>
                  <ul className="space-y-3">
                    {brief?.drivers?.india?.map((news, i) => (
                      <li key={i} className="bg-[var(--bg-primary)] border border-[var(--border-default)] p-4 rounded-xl text-sm text-[var(--text-primary)] leading-relaxed">
                        {news}
                      </li>
                    ))}
                    {(!brief?.drivers?.india || brief.drivers.india.length === 0) && (
                      <li className="text-sm text-[var(--text-muted)] italic">No critical domestic news.</li>
                    )}
                  </ul>
                </div>
              </div>
              
              {/* Critical Risk Alerts Full List */}
              {brief?.risk_alerts && brief.risk_alerts.length > 0 && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-5">
                  <h3 className="text-xs font-black uppercase tracking-widest text-red-400 mb-3 flex items-center gap-2">
                    ⚠️ Critical Risk Alerts
                  </h3>
                  <ul className="space-y-2">
                    {brief.risk_alerts.map((alert, i) => (
                      <li key={i} className="text-sm text-[var(--text-primary)] font-medium leading-relaxed">
                        • {alert}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            </div>
          </div>
        </div>
      )}

    </div>
  );
}

function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="h-6 w-40 bg-[var(--bg-card)] rounded loading-shimmer" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-48 bg-[var(--bg-card)] rounded-lg loading-shimmer border border-[var(--border-default)]" />
        ))}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="h-36 bg-[var(--bg-card)] rounded-lg loading-shimmer border border-[var(--border-default)]" />
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/20 rounded-lg p-6 text-center">
      <p className="text-[var(--accent-red)] font-medium mb-2">Failed to load dashboard</p>
      <p className="text-xs text-[var(--text-muted)]">{message}</p>
      <p className="text-xs text-[var(--text-muted)] mt-2">Ensure backend is running at localhost:8000</p>
    </div>
  );
}
