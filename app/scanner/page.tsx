'use client';

import { useState } from 'react';
import { Search, Filter, SlidersHorizontal, Download, RefreshCw } from 'lucide-react';

export default function ScannerPage() {
  const [filters, setFilters] = useState({
    direction: 'all',
    minConfidence: 60,
    sector: 'all',
    pattern: 'all',
  });

  // Placeholder data for scanner results
  const scannerResults = [
    { symbol: 'RELIANCE', name: 'Reliance Industries', direction: 'LONG', confidence: 82, pattern: 'Bull Flag', sector: 'Energy' },
    { symbol: 'HDFCBANK', name: 'HDFC Bank', direction: 'LONG', confidence: 76, pattern: 'Double Bottom', sector: 'Banking' },
    { symbol: 'ICICIBANK', name: 'ICICI Bank', direction: 'LONG', confidence: 84, pattern: 'Cup & Handle', sector: 'Banking' },
    { symbol: 'INFY', name: 'Infosys', direction: 'SHORT', confidence: 71, pattern: 'Head & Shoulders', sector: 'IT' },
    { symbol: 'TATAMOTORS', name: 'Tata Motors', direction: 'LONG', confidence: 79, pattern: 'Ascending Triangle', sector: 'Auto' },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold">Stock Scanner</h1>
          <p className="text-terminal-muted text-sm mt-1">
            Filter and scan stocks based on technical and fundamental criteria
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="flex items-center gap-2 px-3 py-2 bg-terminal-border rounded text-sm hover:bg-terminal-muted/30 transition-colors">
            <Download className="w-4 h-4" />
            Export
          </button>
          <button className="flex items-center gap-2 px-3 py-2 bg-terminal-accent text-white rounded text-sm hover:bg-terminal-accent/80 transition-colors">
            <RefreshCw className="w-4 h-4" />
            Scan Now
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-terminal-card border border-terminal-border rounded-lg p-4 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <SlidersHorizontal className="w-4 h-4 text-terminal-accent" />
          <span className="font-medium">Filters</span>
        </div>
        <div className="grid grid-cols-4 gap-4">
          <div>
            <label className="text-xs text-terminal-muted uppercase tracking-wider block mb-2">Direction</label>
            <select
              value={filters.direction}
              onChange={(e) => setFilters({ ...filters, direction: e.target.value })}
              className="w-full bg-terminal-bg border border-terminal-border rounded px-3 py-2 text-sm focus:outline-none focus:border-terminal-accent"
            >
              <option value="all">All</option>
              <option value="LONG">Long Only</option>
              <option value="SHORT">Short Only</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-terminal-muted uppercase tracking-wider block mb-2">Min Confidence</label>
            <select
              value={filters.minConfidence}
              onChange={(e) => setFilters({ ...filters, minConfidence: Number(e.target.value) })}
              className="w-full bg-terminal-bg border border-terminal-border rounded px-3 py-2 text-sm focus:outline-none focus:border-terminal-accent"
            >
              <option value={50}>50%+</option>
              <option value={60}>60%+</option>
              <option value={70}>70%+</option>
              <option value={80}>80%+</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-terminal-muted uppercase tracking-wider block mb-2">Sector</label>
            <select
              value={filters.sector}
              onChange={(e) => setFilters({ ...filters, sector: e.target.value })}
              className="w-full bg-terminal-bg border border-terminal-border rounded px-3 py-2 text-sm focus:outline-none focus:border-terminal-accent"
            >
              <option value="all">All Sectors</option>
              <option value="Banking">Banking</option>
              <option value="IT">IT</option>
              <option value="Auto">Auto</option>
              <option value="Energy">Energy</option>
              <option value="Pharma">Pharma</option>
            </select>
          </div>
          <div>
            <label className="text-xs text-terminal-muted uppercase tracking-wider block mb-2">Pattern</label>
            <select
              value={filters.pattern}
              onChange={(e) => setFilters({ ...filters, pattern: e.target.value })}
              className="w-full bg-terminal-bg border border-terminal-border rounded px-3 py-2 text-sm focus:outline-none focus:border-terminal-accent"
            >
              <option value="all">All Patterns</option>
              <option value="Bull Flag">Bull Flag</option>
              <option value="Double Bottom">Double Bottom</option>
              <option value="Cup & Handle">Cup & Handle</option>
              <option value="Head & Shoulders">Head & Shoulders</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results Table */}
      <div className="bg-terminal-card border border-terminal-border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-terminal-border">
              <th className="text-left px-4 py-3 text-xs text-terminal-muted uppercase tracking-wider">Symbol</th>
              <th className="text-left px-4 py-3 text-xs text-terminal-muted uppercase tracking-wider">Name</th>
              <th className="text-left px-4 py-3 text-xs text-terminal-muted uppercase tracking-wider">Direction</th>
              <th className="text-left px-4 py-3 text-xs text-terminal-muted uppercase tracking-wider">Confidence</th>
              <th className="text-left px-4 py-3 text-xs text-terminal-muted uppercase tracking-wider">Pattern</th>
              <th className="text-left px-4 py-3 text-xs text-terminal-muted uppercase tracking-wider">Sector</th>
            </tr>
          </thead>
          <tbody>
            {scannerResults.map((result) => (
              <tr key={result.symbol} className="border-b border-terminal-border hover:bg-terminal-bg/50 cursor-pointer">
                <td className="px-4 py-3 font-medium">{result.symbol}</td>
                <td className="px-4 py-3 text-terminal-muted">{result.name}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    result.direction === 'LONG' 
                      ? 'bg-terminal-success/10 text-terminal-success' 
                      : 'bg-terminal-danger/10 text-terminal-danger'
                  }`}>
                    {result.direction}
                  </span>
                </td>
                <td className="px-4 py-3 mono-nums">{result.confidence}%</td>
                <td className="px-4 py-3 text-terminal-accent">{result.pattern}</td>
                <td className="px-4 py-3 text-terminal-muted">{result.sector}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Backend Ready Notice */}
      <div className="mt-6 p-4 bg-terminal-card border border-terminal-border rounded-lg">
        <div className="text-xs text-terminal-muted uppercase tracking-wider mb-2">Backend Integration</div>
        <div className="text-sm text-terminal-muted">
          This scanner UI is ready to connect to <code className="bg-terminal-bg px-2 py-1 rounded">/api/scanner</code>.
          Filters will be passed as query parameters. Results are paginated and sortable.
        </div>
      </div>
    </div>
  );
}
