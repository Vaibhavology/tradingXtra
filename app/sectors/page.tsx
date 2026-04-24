'use client';

import { mockSectors } from '@/lib/mockData';
import SectorCard from '@/components/SectorCard';
import { TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';

export default function SectorsPage() {
  const bullishCount = mockSectors.filter(s => s.direction === 'bullish').length;
  const bearishCount = mockSectors.filter(s => s.direction === 'bearish').length;
  const neutralCount = mockSectors.filter(s => s.direction === 'neutral').length;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-semibold">Sector Analysis</h1>
        <p className="text-terminal-muted text-sm mt-1">
          Today's expected sector performance based on multi-factor analysis
        </p>
      </div>

      {/* Summary Bar */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-terminal-success/10 border border-terminal-success/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-5 h-5 text-terminal-success" />
            <span className="text-terminal-success font-medium">Bullish</span>
          </div>
          <div className="text-3xl font-bold">{bullishCount}</div>
          <div className="text-sm text-terminal-muted">sectors</div>
        </div>
        <div className="bg-terminal-danger/10 border border-terminal-danger/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="w-5 h-5 text-terminal-danger" />
            <span className="text-terminal-danger font-medium">Bearish</span>
          </div>
          <div className="text-3xl font-bold">{bearishCount}</div>
          <div className="text-sm text-terminal-muted">sectors</div>
        </div>
        <div className="bg-terminal-warning/10 border border-terminal-warning/30 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <Minus className="w-5 h-5 text-terminal-warning" />
            <span className="text-terminal-warning font-medium">Neutral</span>
          </div>
          <div className="text-3xl font-bold">{neutralCount}</div>
          <div className="text-sm text-terminal-muted">sectors</div>
        </div>
      </div>

      {/* Info Box */}
      <div className="mb-6 p-3 bg-terminal-card border border-terminal-border rounded-lg">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-terminal-accent mt-0.5" />
          <div className="text-sm">
            <span className="font-medium text-terminal-accent">Sector Rotation Analysis</span>
            <p className="text-terminal-muted mt-1">
              Sector strength is derived from FII/DII flows, relative performance vs NIFTY, 
              breadth indicators, and fundamental factors. Top picks are selected from 
              the strongest stocks within each sector.
            </p>
          </div>
        </div>
      </div>

      {/* Sector Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {mockSectors.map((sector) => (
          <SectorCard key={sector.name} sector={sector} />
        ))}
      </div>

      {/* API Info */}
      <div className="mt-8 p-4 bg-terminal-card border border-terminal-border rounded-lg">
        <div className="text-xs text-terminal-muted uppercase tracking-wider mb-2">Data Source</div>
        <div className="text-sm text-terminal-muted">
          <code className="bg-terminal-bg px-2 py-1 rounded">/api/sectors</code>
          <span className="ml-2">• Updated every 15 minutes during market hours</span>
        </div>
      </div>
    </div>
  );
}
