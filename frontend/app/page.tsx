"use client";
import { useState } from "react";
import { refreshInvestSmart } from "@/lib/api";
import { useDashboard } from "@/lib/dashboard-cache";
import { Activity, AlertTriangle, Monitor, Globe, MapPin, RefreshCw } from "lucide-react";
import PickCard from "@/components/PickCard";
import PortfolioCard from "@/components/PortfolioCard";
import PerformanceCard from "@/components/PerformanceCard";
import ChartAnalyzerCard from "@/components/ChartAnalyzerCard";

export default function Dashboard() {
  const { scan, brief, portfolio, perf, loading, scanLoading, error, setBrief } = useDashboard();
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
            <div className="space-y-6">
              {/* Status bar */}
              <div className="flex items-center gap-3 px-1">
                <Activity className="w-5 h-5 text-[var(--accent-blue)] animate-pulse" />
                <span className="text-sm text-[var(--text-secondary)] font-medium">Scanning 35 stocks...</span>
                <div className="flex-1 h-1 bg-[var(--bg-secondary)] rounded-full overflow-hidden ml-2 max-w-[200px]">
                  <div className="h-full bg-gradient-to-r from-[var(--accent-blue)] to-[var(--accent-blue)]/40 rounded-full" style={{width: '60%', animation: 'shimmer 2s ease-in-out infinite'}} />
                </div>
              </div>
              {/* Skeleton pick cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 skeleton-stagger">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="rounded-2xl border border-[var(--border-default)] bg-[var(--bg-card)] p-6 space-y-5">
                    {/* Header: symbol + badge */}
                    <div className="flex justify-between items-center">
                      <div className="skeleton-text h-6 w-24" />
                      <div className="skeleton h-6 w-28 rounded-md" />
                    </div>
                    {/* Sector label */}
                    <div className="skeleton-text h-3 w-16" />
                    {/* Probability bar */}
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <div className="skeleton-text h-3 w-14" />
                        <div className="skeleton-text h-3 w-10" />
                      </div>
                      <div className="h-2 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                        <div className="skeleton h-full rounded-full" style={{width: `${40 + i * 10}%`}} />
                      </div>
                    </div>
                    {/* Price row */}
                    <div className="grid grid-cols-3 gap-3 pt-2">
                      {['Entry', 'SL', 'Target'].map(label => (
                        <div key={label} className="space-y-1">
                          <div className="skeleton-text h-2.5 w-10" />
                          <div className="skeleton-text h-5 w-16" />
                        </div>
                      ))}
                    </div>
                    {/* Reasoning section */}
                    <div className="space-y-2 pt-2 border-t border-[var(--border-default)]/30">
                      <div className="skeleton-text h-3 w-full" />
                      <div className="skeleton-text h-3 w-3/4" />
                    </div>
                    {/* Footer: EV */}
                    <div className="flex justify-between items-center pt-2">
                      <div className="skeleton-text h-5 w-20" />
                      <div className="skeleton-text h-4 w-12" />
                    </div>
                  </div>
                ))}
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
            
            {brief?.invest_smart ? (
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
            ) : (
            <div className="group relative bg-[var(--bg-card)] border border-dashed border-[var(--border-default)] rounded-3xl overflow-hidden shadow-lg p-12 lg:p-16 text-center">
               <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent-blue)]/3 via-transparent to-transparent" />
               <div className="relative z-10 flex flex-col items-center gap-4">
                  <Monitor className="w-12 h-12 text-[var(--accent-blue)] opacity-40" />
                  <p className="text-lg text-[var(--text-primary)] font-semibold">No Video Analysis Yet</p>
                  <p className="text-sm text-[var(--text-muted)] max-w-md">Click <strong>&quot;Refresh Video&quot;</strong> above to fetch the latest YouTube market analysis from The Wealth Magnet and get AI-powered insights.</p>
               </div>
            </div>
            )}
         </div>

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
    <div className="space-y-12 max-w-[1600px] mx-auto pb-16">

      {/* ── 1. MARKET STATE HERO SKELETON ─────────────────────────── */}
      <div className="relative overflow-hidden rounded-3xl border border-[var(--border-default)] bg-[var(--bg-card)] p-8 lg:p-12">
        {/* Ambient glow */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] rounded-full bg-[var(--text-muted)] blur-[120px] opacity-[0.06] skeleton-glow" />

        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-end gap-8">
          <div className="space-y-5 flex-1">
            {/* Label */}
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full skeleton" />
              <div className="skeleton-text h-3 w-28" />
            </div>
            {/* Big headline */}
            <div className="skeleton-text h-14 w-72 md:w-96 rounded-xl" />
            {/* Subtitle */}
            <div className="space-y-2">
              <div className="skeleton-text h-5 w-full max-w-lg" />
              <div className="skeleton-text h-5 w-3/4 max-w-md" />
            </div>
          </div>
          {/* System status box */}
          <div className="bg-[var(--bg-primary)]/80 p-4 rounded-xl border border-[var(--border-default)] w-36 space-y-3">
            <div className="skeleton-text h-2.5 w-20" />
            <div className="flex gap-3">
              <div className="space-y-1">
                <div className="skeleton-text h-5 w-8" />
                <div className="skeleton-text h-2 w-12" />
              </div>
              <div className="w-px bg-[var(--border-default)]" />
              <div className="space-y-1">
                <div className="skeleton-text h-5 w-6" />
                <div className="skeleton-text h-2 w-8" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 2. MAIN GRID (Picks + Risk) ──────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">

        {/* LEFT: Actionable Opportunities */}
        <div className="lg:col-span-8 space-y-6">
          {/* Section header */}
          <div className="border-b border-[var(--border-default)]/50 pb-4 space-y-2">
            <div className="skeleton-text h-7 w-64" />
            <div className="skeleton-text h-3 w-40" />
          </div>
          {/* Skeleton pick cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 skeleton-stagger">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="rounded-2xl border border-[var(--border-default)] bg-[var(--bg-card)] p-6 space-y-5">
                <div className="flex justify-between items-center">
                  <div className="skeleton-text h-6 w-24" />
                  <div className="skeleton h-6 w-28 rounded-md" />
                </div>
                <div className="skeleton-text h-3 w-16" />
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <div className="skeleton-text h-3 w-14" />
                    <div className="skeleton-text h-3 w-10" />
                  </div>
                  <div className="h-2 bg-[var(--bg-secondary)] rounded-full overflow-hidden">
                    <div className="skeleton h-full rounded-full" style={{width: `${40 + i * 12}%`}} />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-3 pt-2">
                  {[1, 2, 3].map(j => (
                    <div key={j} className="space-y-1">
                      <div className="skeleton-text h-2.5 w-10" />
                      <div className="skeleton-text h-5 w-16" />
                    </div>
                  ))}
                </div>
                <div className="space-y-2 pt-2 border-t border-[var(--border-default)]/30">
                  <div className="skeleton-text h-3 w-full" />
                  <div className="skeleton-text h-3 w-2/3" />
                </div>
                <div className="flex justify-between items-center pt-2">
                  <div className="skeleton-text h-5 w-20" />
                  <div className="skeleton-text h-4 w-12" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT: Risk Context */}
        <div className="lg:col-span-4 space-y-6">
          {/* Section header */}
          <div className="border-b border-[var(--border-default)]/50 pb-4 space-y-2">
            <div className="skeleton-text h-7 w-36" />
            <div className="skeleton-text h-3 w-32" />
          </div>

          {/* Alert box skeleton */}
          <div className="bg-red-500/5 border border-red-500/10 rounded-2xl p-6 space-y-4">
            <div className="flex justify-between items-center">
              <div className="skeleton-text h-3 w-28" />
              <div className="skeleton h-5 w-16 rounded-md" />
            </div>
            <div className="space-y-3">
              <div className="skeleton-text h-4 w-full" />
              <div className="skeleton-text h-4 w-5/6" />
              <div className="skeleton-text h-4 w-4/6" />
            </div>
          </div>

          {/* Volatility + Sectors */}
          <div className="grid grid-cols-2 gap-5">
            <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl p-6 space-y-3">
              <div className="skeleton-text h-2.5 w-16" />
              <div className="skeleton-text h-9 w-16" />
              <div className="skeleton-text h-2 w-14" />
            </div>
            <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl p-6 space-y-3">
              <div className="skeleton-text h-2.5 w-20" />
              <div className="mt-3 space-y-2">
                <div className="skeleton h-6 w-14 rounded" />
                <div className="skeleton h-6 w-12 rounded" />
              </div>
            </div>
          </div>

          {/* Chart Analyzer skeleton */}
          <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl p-6 space-y-3">
            <div className="flex items-center gap-2">
              <div className="skeleton h-5 w-5 rounded" />
              <div className="skeleton-text h-4 w-28" />
            </div>
            <div className="skeleton-text h-3 w-full" />
            <div className="skeleton h-10 w-full rounded-lg mt-2" />
          </div>
        </div>
      </div>

      {/* ── 3. INVEST SMART SKELETON ─────────────────────────────── */}
      <div className="mt-16 pt-8 border-t border-[var(--border-default)]/30">
        {/* Header */}
        <div className="flex items-end justify-between mb-8">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <div className="skeleton h-8 w-8 rounded-lg" />
              <div className="skeleton-text h-7 w-40" />
            </div>
            <div className="skeleton-text h-3 w-52 ml-11" />
          </div>
          <div className="skeleton h-9 w-36 rounded-xl" />
        </div>
        {/* Content card */}
        <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-3xl p-8 lg:p-10">
          <div className="flex flex-col xl:flex-row gap-10">
            <div className="xl:w-1/3 space-y-5">
              <div className="skeleton-text h-7 w-full" />
              <div className="skeleton-text h-5 w-4/5" />
              <div className="bg-[var(--bg-primary)]/50 p-5 rounded-2xl border border-[var(--border-default)]/50 space-y-2">
                <div className="skeleton-text h-3 w-full" />
                <div className="skeleton-text h-3 w-full" />
                <div className="skeleton-text h-3 w-2/3" />
              </div>
            </div>
            <div className="xl:w-2/3 grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div className="skeleton-text h-3 w-28" />
                {[1, 2, 3].map(i => (
                  <div key={i} className="skeleton-text h-4 w-full" />
                ))}
                <div className="skeleton-text h-3 w-32 mt-6" />
                {[1, 2, 3].map(i => (
                  <div key={i} className="skeleton-text h-4 w-full" />
                ))}
              </div>
              <div className="bg-[var(--bg-primary)]/30 rounded-2xl p-6 border border-[var(--border-default)]/30 space-y-4">
                <div className="skeleton-text h-3 w-28" />
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="bg-[var(--bg-card)] p-4 rounded-xl border border-[var(--border-default)] space-y-2">
                    <div className="flex justify-between">
                      <div className="skeleton-text h-4 w-16" />
                      <div className="skeleton h-5 w-12 rounded-md" />
                    </div>
                    <div className="skeleton-text h-3 w-full" />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── 4. PORTFOLIO + PERFORMANCE SKELETON ──────────────────── */}
      <div className="mt-16 pt-8 border-t border-[var(--border-default)]/30 flex flex-col lg:flex-row gap-6 opacity-50">
        <div className="lg:w-1/2 bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl p-6 space-y-4">
          <div className="skeleton-text h-5 w-24" />
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="space-y-1">
                <div className="skeleton-text h-2.5 w-16" />
                <div className="skeleton-text h-6 w-20" />
              </div>
            ))}
          </div>
        </div>
        <div className="lg:w-1/2 bg-[var(--bg-card)] border border-[var(--border-default)] rounded-2xl p-6 space-y-4">
          <div className="skeleton-text h-5 w-28" />
          <div className="grid grid-cols-2 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="space-y-1">
                <div className="skeleton-text h-2.5 w-16" />
                <div className="skeleton-text h-6 w-20" />
              </div>
            ))}
          </div>
        </div>
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
