"use client";

import { useState, useRef, useEffect } from "react";
import { analyzeStockDetails, StockDetails } from "@/lib/api";
import OrderBookCard from "@/components/OrderBookCard";
import { NSE_STOCKS } from "@/lib/nseStocks";

export default function AnalyzePage() {
  const [query, setQuery] = useState("");
  const [symbol, setSymbol] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState<StockDetails | null>(null);

  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filteredStocks = NSE_STOCKS.filter(stock => 
    stock.name.toLowerCase().includes(query.toLowerCase()) || 
    stock.symbol.toLowerCase().includes(query.toLowerCase())
  ).slice(0, 10);

  const handleSelect = (selectedSymbol: string, selectedName: string) => {
    setSymbol(selectedSymbol);
    setQuery(selectedName);
    setShowDropdown(false);
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const searchTarget = symbol || query;
    if (!searchTarget) return;
    
    setLoading(true);
    setError("");
    setData(null);

    try {
      const result = await analyzeStockDetails(searchTarget.toUpperCase());
      setData(result);
    } catch (err: any) {
      setError(err.message || "Failed to fetch stock details");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full space-y-6">
      {/* HEADER & SEARCH */}
      <div className="flex flex-col md:flex-row md:items-center justify-between terminal-card p-6 rounded-xl border border-[var(--border-default)] shadow-lg relative overflow-hidden gap-4">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-[80px]" />
        
        <div>
          <h1 className="text-3xl font-black text-white tracking-tight">Stock <span className="text-[var(--accent-blue)]">Analyzer</span></h1>
          <p className="text-[var(--text-muted)] text-sm mt-1">Deep-dive intelligence & real-time order book flow.</p>
        </div>

        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row gap-3 z-10 w-full md:w-1/2 relative" ref={dropdownRef}>
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Search company (e.g. State Bank) or symbol"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setSymbol("");
                setShowDropdown(true);
              }}
              onFocus={() => setShowDropdown(true)}
              className="w-full bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded px-4 py-2 text-white focus:outline-none focus:border-[var(--accent-blue)] transition-colors"
            />
            
            {showDropdown && query && filteredStocks.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-[var(--bg-secondary)] border border-[var(--border-default)] rounded-md shadow-xl z-50 max-h-60 overflow-y-auto">
                {filteredStocks.map((s) => (
                  <div
                    key={s.symbol}
                    onClick={() => handleSelect(s.symbol, s.name)}
                    className="px-4 py-2 hover:bg-[var(--bg-primary)] cursor-pointer border-b border-[var(--border-default)] last:border-b-0 flex justify-between items-center"
                  >
                    <span className="text-white text-sm truncate mr-2">{s.name}</span>
                    <span className="text-[var(--text-muted)] text-xs font-mono bg-[var(--bg-card)] px-1.5 py-0.5 rounded shrink-0">{s.symbol}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <button
            type="submit"
            disabled={loading || (!symbol && !query)}
            className="bg-[var(--accent-blue)] text-black px-6 py-2 rounded font-bold uppercase tracking-wider hover:bg-[var(--accent-blue)]/90 disabled:opacity-50 transition-all shrink-0"
          >
            {loading ? "Scanning..." : "Analyze"}
          </button>
        </form>
      </div>

      {error && (
        <div className="p-4 bg-[var(--accent-red)]/10 border border-[var(--accent-red)]/30 rounded text-[var(--accent-red)] font-mono text-sm">
          [ERROR]: {error}
        </div>
      )}

      {/* RESULTS */}
      {data && (
        <div className="flex flex-col lg:flex-row gap-6">
          {/* LEFT SIDE: INTELLIGENCE */}
          <div className="lg:w-[70%] space-y-6">
            
            {/* Overview Profile */}
            <div className="terminal-card p-6 rounded-xl border border-[var(--border-default)] shadow-lg relative overflow-hidden">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-white uppercase">{data.name}</h2>
                  <div className="flex gap-2 mt-2">
                    <span className="px-2 py-0.5 bg-[var(--bg-secondary)] rounded text-xs font-mono text-[var(--text-muted)] uppercase border border-[var(--border-default)]">{data.symbol}</span>
                    <span className="px-2 py-0.5 bg-[var(--bg-secondary)] rounded text-xs font-mono text-[var(--text-muted)] uppercase border border-[var(--border-default)]">{data.sector}</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-mono text-white">₹{data.current_price?.toLocaleString('en-IN', { minimumFractionDigits: 2 }) || 'N/A'}</div>
                  <div className="text-xs text-[var(--text-muted)] uppercase mt-1">LTP</div>
                </div>
              </div>
              
              <p className="text-[var(--text-muted)] text-sm leading-relaxed mb-6">
                {data.description}
              </p>

              <div className="grid grid-cols-3 gap-4 border-t border-[var(--border-default)] pt-4">
                <div>
                  <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold tracking-wider">Market Cap</div>
                  <div className="font-mono text-white mt-1">
                    {data.market_cap ? `₹${(data.market_cap / 10000000).toFixed(2)} Cr` : 'N/A'}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold tracking-wider">P/E Ratio</div>
                  <div className="font-mono text-white mt-1">{data.pe_ratio !== "N/A" ? Number(data.pe_ratio).toFixed(2) : 'N/A'}</div>
                </div>
                <div>
                  <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold tracking-wider">Next Earnings Date</div>
                  <div className="font-mono text-[var(--accent-blue)] mt-1">{data.next_earnings_date}</div>
                </div>
              </div>
            </div>

            {/* AI Assessment */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Strengths & Weaknesses */}
              <div className="terminal-card p-6 rounded-xl border border-[var(--border-default)] shadow-lg">
                 <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-[var(--border-default)] pb-2">Profile Matrix</h3>
                 
                 <div className="space-y-4">
                   <div>
                     <div className="text-[10px] uppercase text-[var(--accent-green)] font-bold mb-2">Strengths</div>
                     <ul className="space-y-1">
                       {data.strengths.map((s, i) => (
                         <li key={i} className="text-sm text-[var(--text-muted)] flex items-start gap-2">
                           <span className="text-[var(--accent-green)]">✓</span> {s}
                         </li>
                       ))}
                     </ul>
                   </div>
                   
                   <div>
                     <div className="text-[10px] uppercase text-[var(--accent-red)] font-bold mb-2">Weaknesses</div>
                     <ul className="space-y-1">
                       {data.weaknesses.map((w, i) => (
                         <li key={i} className="text-sm text-[var(--text-muted)] flex items-start gap-2">
                           <span className="text-[var(--accent-red)]">✗</span> {w}
                         </li>
                       ))}
                     </ul>
                   </div>
                 </div>
              </div>

              {/* Verdict */}
              <div className="terminal-card p-6 rounded-xl border border-[var(--border-default)] shadow-lg flex flex-col">
                 <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-[var(--border-default)] pb-2">Investment Verdict</h3>
                 
                 <div className="flex-1 space-y-6">
                    <div>
                      <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold mb-2">Can we invest?</div>
                      <div className={`p-3 rounded border text-sm font-medium ${
                        data.can_invest.includes('Yes') ? 'bg-[var(--accent-green)]/10 border-[var(--accent-green)]/30 text-[var(--accent-green)]' :
                        data.can_invest.includes('Caution') ? 'bg-[var(--accent-red)]/10 border-[var(--accent-red)]/30 text-[var(--accent-red)]' :
                        'bg-yellow-500/10 border-yellow-500/30 text-yellow-500'
                      }`}>
                        {data.can_invest}
                      </div>
                    </div>

                    <div>
                      <div className="text-[10px] uppercase text-[var(--text-muted)] font-bold mb-2 flex items-center justify-between">
                        Risk Analysis
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          data.risk_level === 'High' ? 'bg-[var(--accent-red)] text-white' :
                          data.risk_level === 'Low' ? 'bg-[var(--accent-green)] text-black' :
                          'bg-yellow-500 text-black'
                        }`}>
                          {data.risk_level} RISK
                        </span>
                      </div>
                      <p className="text-sm text-[var(--text-muted)] leading-relaxed">
                        {data.risk_analysis}
                      </p>
                    </div>
                 </div>
              </div>
            </div>

          </div>

          {/* RIGHT SIDE: ORDER BOOK */}
          <div className="lg:w-[30%] h-[600px]">
             <OrderBookCard symbol={data.symbol} />
          </div>
        </div>
      )}
      
      {/* EMPTY STATE */}
      {!data && !loading && !error && (
        <div className="flex-1 flex flex-col items-center justify-center text-[var(--text-muted)] border border-dashed border-[var(--border-default)] rounded-xl py-20">
          <svg className="w-16 h-16 mb-4 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <p className="text-sm uppercase tracking-wider font-bold opacity-50">Enter a symbol to view deep analysis</p>
        </div>
      )}
    </div>
  );
}
