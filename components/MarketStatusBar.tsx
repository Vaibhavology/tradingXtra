'use client';

import { MarketStatus } from '@/types';
import { TrendingUp, TrendingDown, Clock, AlertTriangle } from 'lucide-react';

interface MarketStatusBarProps {
  data: MarketStatus;
}

export default function MarketStatusBar({ data }: MarketStatusBarProps) {
  const formatTime = (isoString: string) => {
    return new Date(isoString).toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'decimal',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  return (
    <div className="bg-terminal-card border border-terminal-border rounded-lg p-4 mb-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        {/* NIFTY */}
        <div className="flex items-center gap-3">
          <div className="text-xs text-terminal-muted uppercase tracking-wider">NIFTY 50</div>
          <div className="flex items-center gap-2">
            <span className="mono-nums font-medium">{formatCurrency(data.nifty.value)}</span>
            <div className={`flex items-center gap-1 text-sm ${
              data.nifty.direction === 'up' ? 'text-terminal-success' : 'text-terminal-danger'
            }`}>
              {data.nifty.direction === 'up' ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              <span className="mono-nums">{data.nifty.change > 0 ? '+' : ''}{data.nifty.change}%</span>
            </div>
          </div>
        </div>

        {/* BANKNIFTY */}
        <div className="flex items-center gap-3">
          <div className="text-xs text-terminal-muted uppercase tracking-wider">BANKNIFTY</div>
          <div className="flex items-center gap-2">
            <span className="mono-nums font-medium">{formatCurrency(data.bankNifty.value)}</span>
            <div className={`flex items-center gap-1 text-sm ${
              data.bankNifty.direction === 'up' ? 'text-terminal-success' : 'text-terminal-danger'
            }`}>
              {data.bankNifty.direction === 'up' ? (
                <TrendingUp className="w-4 h-4" />
              ) : (
                <TrendingDown className="w-4 h-4" />
              )}
              <span className="mono-nums">{data.bankNifty.change > 0 ? '+' : ''}{data.bankNifty.change}%</span>
            </div>
          </div>
        </div>

        {/* India VIX */}
        <div className="flex items-center gap-3">
          <div className="text-xs text-terminal-muted uppercase tracking-wider">VIX</div>
          <div className="flex items-center gap-2">
            <span className="mono-nums font-medium">{data.indiaVix.value}</span>
            <span className={`mono-nums text-sm ${
              data.indiaVix.change < 0 ? 'text-terminal-success' : 'text-terminal-danger'
            }`}>
              {data.indiaVix.change > 0 ? '+' : ''}{data.indiaVix.change}%
            </span>
          </div>
        </div>

        {/* FII/DII Flow */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-terminal-muted">FII</span>
            <span className={`mono-nums text-sm font-medium ${
              data.fiiFlow.type === 'buy' ? 'text-terminal-success' : 'text-terminal-danger'
            }`}>
              {data.fiiFlow.type === 'buy' ? '+' : '-'}₹{formatCurrency(data.fiiFlow.value)}Cr
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-terminal-muted">DII</span>
            <span className={`mono-nums text-sm font-medium ${
              data.diiFlow.type === 'buy' ? 'text-terminal-success' : 'text-terminal-danger'
            }`}>
              {data.diiFlow.type === 'buy' ? '+' : '-'}₹{formatCurrency(data.diiFlow.value)}Cr
            </span>
          </div>
        </div>

        {/* Last Updated */}
        <div className="flex items-center gap-2 text-terminal-muted">
          <Clock className="w-4 h-4" />
          <span className="text-xs">{formatTime(data.lastUpdated)}</span>
          {data.marketOpen ? (
            <span className="text-xs text-terminal-success">● Open</span>
          ) : (
            <span className="text-xs text-terminal-warning">● Closed</span>
          )}
        </div>
      </div>
    </div>
  );
}
