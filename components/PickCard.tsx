'use client';

import { StockPick } from '@/types';
import { TrendingUp, TrendingDown, AlertTriangle, Eye, MessageSquare, BarChart3, Shield } from 'lucide-react';
import PatternBadge from './PatternBadge';

interface PickCardProps {
  pick: StockPick;
  onOpenChart: (pick: StockPick) => void;
  onAskAI: (pick: StockPick) => void;
  onWatch: (pick: StockPick) => void;
}

export default function PickCard({ pick, onOpenChart, onAskAI, onWatch }: PickCardProps) {
  const isLong = pick.direction === 'LONG';
  const directionColor = isLong ? 'text-terminal-success' : 'text-terminal-danger';
  const directionBg = isLong ? 'bg-terminal-success/10' : 'bg-terminal-danger/10';

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'text-terminal-success';
    if (confidence >= 65) return 'text-terminal-warning';
    return 'text-terminal-danger';
  };

  const getCrossCheckBadge = () => {
    if (pick.crossCheck.status === 'OK') {
      return (
        <div className="flex items-center gap-1 text-xs text-terminal-success">
          <Shield className="w-3 h-3" />
          <span>Verified</span>
        </div>
      );
    }
    if (pick.crossCheck.status === 'WARNING') {
      return (
        <div className="flex items-center gap-1 text-xs text-terminal-warning" title={pick.crossCheck.issues.join(', ')}>
          <AlertTriangle className="w-3 h-3" />
          <span>Warning</span>
        </div>
      );
    }
    return (
      <div className="flex items-center gap-1 text-xs text-terminal-danger">
        <AlertTriangle className="w-3 h-3" />
        <span>Critical</span>
      </div>
    );
  };

  return (
    <div className="pick-card bg-terminal-card border border-terminal-border rounded-lg p-4 flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-lg">{pick.symbol}</h3>
            <span className={`px-2 py-0.5 rounded text-xs font-medium ${directionBg} ${directionColor}`}>
              {pick.direction}
            </span>
            <span className="px-2 py-0.5 rounded text-xs bg-terminal-border text-terminal-muted">
              {pick.sector}
            </span>
          </div>
          <p className="text-sm text-terminal-muted">{pick.name}</p>
        </div>
        <div className="text-right">
          {pick.currentPrice ? (
            <>
              <div className="text-xl font-bold mono-nums">₹{formatPrice(pick.currentPrice)}</div>
              <div className="text-xs text-terminal-muted">Current Price</div>
            </>
          ) : (
            <>
              <div className={`text-2xl font-bold mono-nums ${getConfidenceColor(pick.confidence)}`}>
                {pick.confidence}
              </div>
              <div className="text-xs text-terminal-muted">Confidence</div>
            </>
          )}
        </div>
      </div>

      {/* Key Metrics row */}
      <div className="flex items-center gap-3 mb-3 text-xs">
        {pick.currentPrice && (
          <div className={`px-2 py-1 rounded ${getConfidenceColor(pick.confidence)} bg-terminal-bg`}>
            <span className="text-terminal-muted">Score: </span>
            <span className="font-medium">{pick.confidence}%</span>
          </div>
        )}
        {pick.momentumScore && (
          <div className="px-2 py-1 rounded bg-terminal-bg">
            <span className="text-terminal-muted">Mom: </span>
            <span className="font-medium text-terminal-accent">{pick.momentumScore.toFixed(0)}</span>
          </div>
        )}
        {pick.volumeMultiple && (
          <div className="px-2 py-1 rounded bg-terminal-bg">
            <span className="text-terminal-muted">Vol: </span>
            <span className="font-medium text-terminal-accent">{pick.volumeMultiple.toFixed(1)}×</span>
          </div>
        )}
      </div>

      {/* Cross-check Status */}
      {pick.crossCheck.status !== 'OK' && (
        <div className="mb-3 p-2 rounded bg-terminal-warning/10 border border-terminal-warning/30">
          <div className="flex items-center gap-2 text-terminal-warning text-xs">
            <AlertTriangle className="w-4 h-4" />
            <span className="font-medium">Cross-Platform Warning</span>
          </div>
          <ul className="mt-1 text-xs text-terminal-muted">
            {pick.crossCheck.issues.map((issue, i) => (
              <li key={i}>• {issue}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Price Levels */}
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div className="bg-terminal-bg rounded p-2">
          <div className="text-xs text-terminal-muted mb-1">Entry Zone</div>
          <div className="mono-nums text-sm font-medium">
            ₹{formatPrice(pick.entryZone.low)} - ₹{formatPrice(pick.entryZone.high)}
          </div>
        </div>
        <div className="bg-terminal-danger/10 rounded p-2">
          <div className="text-xs text-terminal-danger mb-1">Stop Loss</div>
          <div className="mono-nums text-sm font-medium text-terminal-danger">
            ₹{formatPrice(pick.stopLoss)}
          </div>
        </div>
        <div className="bg-terminal-success/10 rounded p-2">
          <div className="text-xs text-terminal-success mb-1">Target 1</div>
          <div className="mono-nums text-sm font-medium text-terminal-success">
            ₹{formatPrice(pick.target1)}
          </div>
        </div>
        <div className="bg-terminal-success/10 rounded p-2">
          <div className="text-xs text-terminal-success mb-1">Target 2</div>
          <div className="mono-nums text-sm font-medium text-terminal-success">
            ₹{formatPrice(pick.target2)}
          </div>
        </div>
      </div>

      {/* Expected Move & R:R */}
      <div className="flex items-center gap-4 mb-3 text-sm">
        <div className="flex items-center gap-1">
          {isLong ? (
            <TrendingUp className="w-4 h-4 text-terminal-success" />
          ) : (
            <TrendingDown className="w-4 h-4 text-terminal-danger" />
          )}
          <span className={directionColor}>+{pick.expectedMove}%</span>
          <span className="text-terminal-muted">expected</span>
        </div>
        <div className="text-terminal-muted">
          R:R <span className="text-terminal-text font-medium">{pick.riskReward}x</span>
        </div>
        {getCrossCheckBadge()}
      </div>

      {/* Pattern */}
      {pick.pattern && (
        <div className="mb-3">
          <PatternBadge pattern={pick.pattern} />
        </div>
      )}

      {/* Reasoning */}
      <div className="mb-4 flex-grow">
        <div className="text-xs text-terminal-muted uppercase tracking-wider mb-1">Why This Pick</div>
        <ul className="text-sm text-terminal-text space-y-1">
          {pick.reasoning.map((reason, i) => (
            <li key={i} className="flex items-start gap-2">
              <span className="text-terminal-accent mt-1">•</span>
              <span>{reason}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 pt-3 border-t border-terminal-border">
        <button
          onClick={() => onOpenChart(pick)}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-terminal-accent/10 text-terminal-accent rounded text-sm hover:bg-terminal-accent/20 transition-colors"
        >
          <BarChart3 className="w-4 h-4" />
          Chart
        </button>
        <button
          onClick={() => onAskAI(pick)}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-terminal-border text-terminal-text rounded text-sm hover:bg-terminal-muted/30 transition-colors"
        >
          <MessageSquare className="w-4 h-4" />
          Ask AI
        </button>
        <button
          onClick={() => onWatch(pick)}
          className="flex items-center justify-center gap-2 px-3 py-2 bg-terminal-border text-terminal-text rounded text-sm hover:bg-terminal-muted/30 transition-colors"
        >
          <Eye className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
