'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import MarketStatusBar from '@/components/MarketStatusBar';
import PickCard from '@/components/PickCard';
import ChartModal from '@/components/ChartModal';
import InvestSmartCard from '@/components/InvestSmart';
import { mockMarketStatus, mockTodayPicks } from '@/lib/mockData';
import { StockPick, MarketStatus, InvestSmart } from '@/types';
import { AlertTriangle, Shield, RefreshCw, Wifi, WifiOff, Activity, TrendingUp, Zap } from 'lucide-react';

// Adapter: convert backend response → frontend StockPick type
function adaptPick(p: any, idx: number): StockPick {
  return {
    id: String(idx + 1),
    symbol: p.symbol,
    name: p.name,
    direction: p.direction,
    entryZone: { low: p.entry?.[0] ?? 0, high: p.entry?.[1] ?? 0 },
    stopLoss: p.sl,
    target1: p.targets?.[0] ?? 0,
    target2: p.targets?.[1] ?? 0,
    expectedMove: p.expected_move,
    confidence: Math.round((p.confidence ?? 0) * 100),
    pattern: undefined,
    reasoning: p.reasons ?? [],
    crossCheck: {
      status: p.warnings?.length ? 'WARNING' : 'OK',
      issues: p.warnings ?? [],
      platformsChecked: 4,
    },
    riskReward: parseFloat(
      (Math.abs((p.targets?.[0] ?? 0) - (p.entry?.[0] ?? 0)) /
        Math.abs((p.entry?.[0] ?? 0) - p.sl || 1)).toFixed(1)
    ),
    sector: p.sector,
    currentPrice: p.entry?.[0] ?? 0,  // entry[0] is the current price
    momentumScore: p.momentum_score,
    volumeMultiple: p.volume_multiple,
  };
}

function adaptMarketStatus(m: any): MarketStatus {
  return {
    nifty: {
      value: m.nifty_value,
      change: parseFloat(m.nifty?.replace('%', '') ?? '0'),
      direction: m.nifty?.startsWith('+') ? 'up' : 'down',
    },
    bankNifty: {
      value: m.bank_nifty_value,
      change: parseFloat(m.bank_nifty?.replace('%', '') ?? '0'),
      direction: m.bank_nifty?.startsWith('+') ? 'up' : 'down',
    },
    indiaVix: { value: m.vix, change: m.vix_change },
    fiiFlow: {
      value: parseFloat(m.fii_flow?.replace(/[^0-9.]/g, '') ?? '0'),
      type: m.fii_flow?.startsWith('+') ? 'buy' : 'sell',
    },
    diiFlow: {
      value: parseFloat(m.dii_flow?.replace(/[^0-9.]/g, '') ?? '0'),
      type: m.dii_flow?.startsWith('+') ? 'buy' : 'sell',
    },
    lastUpdated: m.timestamp ?? new Date().toISOString(),
    marketOpen: m.market_open ?? true,
  };
}

export default function HomePage() {
  const router = useRouter();
  const [selectedPick, setSelectedPick] = useState<StockPick | null>(null);
  const [picks, setPicks] = useState<StockPick[]>(mockTodayPicks);
  const [marketStatus, setMarketStatus] = useState<MarketStatus>(mockMarketStatus);
  const [loading, setLoading] = useState(true);
  const [isLive, setIsLive] = useState(false);
  const [meta, setMeta] = useState<any>(null);
  const [investSmart, setInvestSmart] = useState<InvestSmart | null>(null);
  const [marketBrief, setMarketBrief] = useState<any>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [mkt, picksData, briefData] = await Promise.all([
        fetch('http://localhost:8000/api/market-status').then(r => r.json()),
        fetch('http://localhost:8000/api/today-picks').then(r => r.json()),
        fetch('http://localhost:8000/api/market-brief').then(r => r.json()).catch(() => null),
      ]);
      setMarketStatus(adaptMarketStatus(mkt));
      setPicks(picksData.picks.map(adaptPick));
      setMeta({
        total: picksData.total_candidates,
        passedMomentum: picksData.passed_momentum_gate,
        passedVolume: picksData.passed_volume_gate,
        passedSector: picksData.passed_sector_gate,
        final: picksData.final_count,
        regime: picksData.market_regime,
      });
      if (briefData) {
        setMarketBrief(briefData);
        if (briefData.invest_smart) {
          setInvestSmart(briefData.invest_smart);
        }
      }
      setIsLive(true);
    } catch {
      // Backend unreachable — fall back to mock
      setPicks(mockTodayPicks);
      setMarketStatus(mockMarketStatus);
      setIsLive(false);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const warningCount = picks.filter(p => p.crossCheck.status !== 'OK').length;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <MarketStatusBar data={marketStatus} />

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold">Today's Top Picks</h1>
          <p className="text-terminal-muted text-sm mt-1">
            Final decisions from the Momentum Decision Engine
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Live / Mock badge */}
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm border ${
            isLive
              ? 'bg-terminal-success/10 border-terminal-success/30 text-terminal-success'
              : 'bg-terminal-warning/10 border-terminal-warning/30 text-terminal-warning'
          }`}>
            {isLive ? <Wifi className="w-4 h-4" /> : <WifiOff className="w-4 h-4" />}
            {isLive ? 'Backend Live' : 'Mock Data'}
          </div>

          {picks.length - warningCount > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-terminal-success/10 border border-terminal-success/30 rounded text-sm">
              <Shield className="w-4 h-4 text-terminal-success" />
              <span className="text-terminal-success">{picks.length - warningCount} Verified</span>
            </div>
          )}
          {warningCount > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-terminal-warning/10 border border-terminal-warning/30 rounded text-sm">
              <AlertTriangle className="w-4 h-4 text-terminal-warning" />
              <span className="text-terminal-warning">{warningCount} Warnings</span>
            </div>
          )}
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 bg-terminal-border rounded text-sm hover:bg-terminal-muted/30 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Gate stats (only when live) */}
      {isLive && meta && (
        <div className="grid grid-cols-5 gap-3 mb-5">
          {[
            { label: 'Universe', value: meta.total },
            { label: 'Momentum Gate', value: meta.passedMomentum },
            { label: 'Volume Gate', value: meta.passedVolume },
            { label: 'Sector Gate', value: meta.passedSector },
            { label: 'Final Picks', value: meta.final, highlight: true },
          ].map(item => (
            <div key={item.label} className={`rounded-lg p-3 border text-center ${
              item.highlight
                ? 'bg-terminal-accent/10 border-terminal-accent/30'
                : 'bg-terminal-card border-terminal-border'
            }`}>
              <div className={`text-2xl font-bold mono-nums ${item.highlight ? 'text-terminal-accent' : ''}`}>
                {item.value}
              </div>
              <div className="text-xs text-terminal-muted mt-1">{item.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Market Intelligence (from market-brief) */}
      {isLive && marketBrief ? (
        <div className="mb-5 space-y-3">
          {/* Bias + Regime row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className={`p-3 rounded-lg border ${
              marketBrief.bias === 'Bullish' ? 'bg-terminal-success/10 border-terminal-success/30' :
              marketBrief.bias === 'Bearish' ? 'bg-terminal-danger/10 border-terminal-danger/30' :
              'bg-terminal-warning/10 border-terminal-warning/30'
            }`}>
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp className="w-4 h-4" />
                <span className="text-xs text-terminal-muted">Market Bias</span>
              </div>
              <div className="font-bold text-lg">{marketBrief.bias}</div>
              <div className="text-xs text-terminal-muted">{marketBrief.behavior ?? ''}</div>
            </div>

            <div className="p-3 rounded-lg border bg-terminal-card border-terminal-border">
              <div className="flex items-center gap-2 mb-1">
                <Activity className="w-4 h-4 text-terminal-accent" />
                <span className="text-xs text-terminal-muted">Regime</span>
              </div>
              <div className="font-bold text-lg capitalize">{marketBrief.regime?.regime ?? meta?.regime ?? 'Unknown'}</div>
              <div className="text-xs text-terminal-muted">
                NIFTY 5d: {marketBrief.nifty_return_5d > 0 ? '+' : ''}{marketBrief.nifty_return_5d?.toFixed(1)}%
                {marketBrief.vix ? ` | VIX: ${marketBrief.vix.toFixed(1)}` : ''}
              </div>
            </div>

            {/* Sectors */}
            <div className="p-3 rounded-lg border bg-terminal-card border-terminal-border">
              <div className="flex items-center gap-2 mb-1">
                <Zap className="w-4 h-4 text-terminal-accent" />
                <span className="text-xs text-terminal-muted">Sector View</span>
              </div>
              {marketBrief.sector_strength?.strong?.length > 0 && (
                <div className="text-xs">
                  <span className="text-terminal-success">Strong: </span>
                  <span className="text-terminal-muted">{marketBrief.sector_strength.strong.join(', ')}</span>
                </div>
              )}
              {marketBrief.sector_strength?.weak?.length > 0 && (
                <div className="text-xs mt-0.5">
                  <span className="text-terminal-danger">Weak: </span>
                  <span className="text-terminal-muted">{marketBrief.sector_strength.weak.join(', ')}</span>
                </div>
              )}
            </div>
          </div>

          {/* Risk Alerts */}
          {marketBrief.risk_alerts?.length > 0 && (
            <div className="p-3 bg-terminal-danger/5 border border-terminal-danger/20 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-terminal-danger" />
                <span className="text-sm font-medium text-terminal-danger">Risk Alerts</span>
              </div>
              <ul className="text-xs text-terminal-muted space-y-0.5">
                {marketBrief.risk_alerts.map((alert: string, i: number) => (
                  <li key={i}>• {alert}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Guidance */}
          {marketBrief.guidance?.length > 0 && (
            <div className="p-3 bg-terminal-accent/5 border border-terminal-accent/20 rounded-lg">
              <div className="flex items-start gap-3">
                <Shield className="w-5 h-5 text-terminal-accent mt-0.5" />
                <div>
                  <span className="text-sm font-medium text-terminal-accent">Today's Trading Guidance</span>
                  <ul className="text-sm text-terminal-muted mt-1 space-y-0.5">
                    {marketBrief.guidance.map((g: string, i: number) => (
                      <li key={i}>• {g}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Static fallback */
        <div className="mb-5 p-3 bg-terminal-accent/5 border border-terminal-accent/20 rounded-lg">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-terminal-accent mt-0.5" />
            <div className="text-sm">
              <span className="font-medium text-terminal-accent">Momentum Decision Engine</span>
              <p className="text-terminal-muted mt-0.5">
                All picks passed: Momentum Gate (≥4% move) → Volume Gate (≥1.5× avg) → Sector Gate (outperforming NIFTY) → Manipulation Filter → Risk Rules.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Picks grid */}
      {loading ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="bg-terminal-card border border-terminal-border rounded-lg h-64 animate-pulse" />
          ))}
        </div>
      ) : picks.length === 0 ? (
        <div className="text-center py-16 text-terminal-muted">
          <AlertTriangle className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>No stocks passed all momentum gates today.</p>
          <p className="text-sm mt-1">Market may be in a low-momentum regime.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {picks.map(pick => (
            <PickCard
              key={pick.id}
              pick={pick}
              onOpenChart={setSelectedPick}
              onAskAI={p => router.push(`/chat?stock=${p.symbol}`)}
              onWatch={p => console.log('Watch:', p.symbol)}
            />
          ))}
        </div>
      )}

      {/* Invest Smart Panel */}
      {investSmart && (
        <div className="mt-6">
          <InvestSmartCard data={investSmart} />
        </div>
      )}

      {/* Disclaimer */}
      <div className="mt-8 p-4 bg-terminal-card border border-terminal-border rounded-lg">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-terminal-warning mt-0.5" />
          <p className="text-sm text-terminal-muted">
            Research-based suggestions only. Always use stop-losses as indicated.
            Past performance does not guarantee future results.
          </p>
        </div>
      </div>

      {selectedPick && (
        <ChartModal pick={selectedPick} onClose={() => setSelectedPick(null)} />
      )}
    </div>
  );
}
