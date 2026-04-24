'use client';

import { StockPick } from '@/types';
import { X, TrendingUp, TrendingDown, AlertTriangle, ExternalLink } from 'lucide-react';

interface ChartModalProps {
  pick: StockPick;
  onClose: () => void;
}

export default function ChartModal({ pick, onClose }: ChartModalProps) {
  const isLong = pick.direction === 'LONG';

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-IN', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm">
      <div className="bg-terminal-card border border-terminal-border rounded-lg w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-terminal-border">
          <div className="flex items-center gap-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-semibold">{pick.symbol}</h2>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  isLong ? 'bg-terminal-success/10 text-terminal-success' : 'bg-terminal-danger/10 text-terminal-danger'
                }`}>
                  {pick.direction}
                </span>
              </div>
              <p className="text-sm text-terminal-muted">{pick.name}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-terminal-border rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          <div className="grid grid-cols-3 gap-4">
            {/* Chart Area */}
            <div className="col-span-2">
              <div className="bg-terminal-bg border border-terminal-border rounded-lg h-96 flex items-center justify-center">
                {/* TradingView Widget Placeholder */}
                <div className="text-center text-terminal-muted">
                  <div className="text-4xl mb-2">📈</div>
                  <p className="text-sm">TradingView Chart</p>
                  <p className="text-xs mt-1">NSE:{pick.symbol}</p>
                  <a
                    href={`https://www.tradingview.com/chart/?symbol=NSE:${pick.symbol}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 mt-3 text-terminal-accent text-sm hover:underline"
                  >
                    Open in TradingView <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>

              {/* Annotation Overlay Info */}
              <div className="mt-4 p-3 bg-terminal-bg border border-terminal-border rounded-lg">
                <div className="text-xs text-terminal-muted uppercase tracking-wider mb-2">Backend Annotations</div>
                <div className="grid grid-cols-4 gap-3 text-sm">
                  <div>
                    <span className="text-terminal-muted">Entry: </span>
                    <span className="mono-nums text-terminal-accent">
                      ₹{formatPrice(pick.entryZone.low)} - ₹{formatPrice(pick.entryZone.high)}
                    </span>
                  </div>
                  <div>
                    <span className="text-terminal-muted">SL: </span>
                    <span className="mono-nums text-terminal-danger">₹{formatPrice(pick.stopLoss)}</span>
                  </div>
                  <div>
                    <span className="text-terminal-muted">T1: </span>
                    <span className="mono-nums text-terminal-success">₹{formatPrice(pick.target1)}</span>
                  </div>
                  <div>
                    <span className="text-terminal-muted">T2: </span>
                    <span className="mono-nums text-terminal-success">₹{formatPrice(pick.target2)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Side Panel */}
            <div className="space-y-4">
              {/* Pattern Info */}
              {pick.pattern && (
                <div className="bg-terminal-bg border border-terminal-border rounded-lg p-3">
                  <div className="text-xs text-terminal-muted uppercase tracking-wider mb-2">Pattern Detected</div>
                  <div className="text-lg font-medium mb-1">{pick.pattern.name}</div>
                  <div className="flex items-center gap-2 text-sm text-terminal-muted mb-3">
                    <span>{pick.pattern.timeframe}</span>
                    <span>•</span>
                    <span className="text-terminal-accent">{pick.pattern.confidence}% confidence</span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-terminal-muted">Support: </span>
                      <span className="mono-nums text-terminal-success">
                        {pick.pattern.keyLevels.support.map(s => `₹${s}`).join(', ')}
                      </span>
                    </div>
                    <div>
                      <span className="text-terminal-muted">Resistance: </span>
                      <span className="mono-nums text-terminal-danger">
                        {pick.pattern.keyLevels.resistance.map(r => `₹${r}`).join(', ')}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Trade Setup */}
              <div className="bg-terminal-bg border border-terminal-border rounded-lg p-3">
                <div className="text-xs text-terminal-muted uppercase tracking-wider mb-2">Trade Setup</div>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-terminal-muted">Direction</span>
                    <span className={isLong ? 'text-terminal-success' : 'text-terminal-danger'}>
                      {pick.direction}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-terminal-muted">Expected Move</span>
                    <span className="text-terminal-success">+{pick.expectedMove}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-terminal-muted">Risk:Reward</span>
                    <span>{pick.riskReward}x</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-terminal-muted">Confidence</span>
                    <span className="text-terminal-accent">{pick.confidence}%</span>
                  </div>
                </div>
              </div>

              {/* Cross-Check Status */}
              <div className={`border rounded-lg p-3 ${
                pick.crossCheck.status === 'OK' 
                  ? 'bg-terminal-success/5 border-terminal-success/30' 
                  : 'bg-terminal-warning/5 border-terminal-warning/30'
              }`}>
                <div className="text-xs text-terminal-muted uppercase tracking-wider mb-2">Cross-Platform Check</div>
                <div className="flex items-center gap-2 mb-2">
                  {pick.crossCheck.status === 'OK' ? (
                    <>
                      <div className="w-2 h-2 rounded-full bg-terminal-success" />
                      <span className="text-terminal-success text-sm">Verified</span>
                    </>
                  ) : (
                    <>
                      <AlertTriangle className="w-4 h-4 text-terminal-warning" />
                      <span className="text-terminal-warning text-sm">Warning</span>
                    </>
                  )}
                </div>
                <div className="text-xs text-terminal-muted">
                  {pick.crossCheck.platformsChecked} platforms checked
                </div>
                {pick.crossCheck.issues.length > 0 && (
                  <ul className="mt-2 text-xs text-terminal-warning space-y-1">
                    {pick.crossCheck.issues.map((issue, i) => (
                      <li key={i}>• {issue}</li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Reasoning */}
              <div className="bg-terminal-bg border border-terminal-border rounded-lg p-3">
                <div className="text-xs text-terminal-muted uppercase tracking-wider mb-2">Reasoning</div>
                <ul className="text-sm space-y-2">
                  {pick.reasoning.map((reason, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-terminal-accent">•</span>
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
