const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  return res.json();
}

// ── API Types ──────────────────────────────────────────────────────

export interface ScanResult {
  results: Array<TradeDecision>;
  accepted: number;
  rejected: number;
  total: number;
}

export interface TradeDecision {
  symbol: string;
  name: string;
  sector: string;
  score: number;
  probability: number;
  ev: number;
  entry: number;
  stop_loss: number;
  target: number;
  atr: number;
  decision: "ACCEPT" | "REJECT";
  regime: string;
  risk_reward: number;
  rejection_reason?: string;
  agents?: Record<string, unknown>;
}

export interface MarketBrief {
  bias: string;
  behavior: string;
  nifty_return_5d: number;
  nifty_return_1d: number;
  vix: number | null;
  usd_inr?: { price: number; change_pct: number };
  scores: {
    global_score: number;
    india_score: number;
    volatility_score: number;
    bias_score: number;
  };
  regime: Record<string, unknown>;
  drivers: {
    global: string[];
    india: string[];
  };
  sector_strength: {
    strong: string[];
    weak: string[];
  };
  risk_alerts: string[];
  guidance: string[];
  invest_smart: InvestSmart | null;
  timestamp: string;
}

export interface InvestSmart {
  title: string;
  published: string;
  link: string;
  stocks: Array<{
    symbol: string;
    action: string;
    reason: string;
    confidence: number;
    in_universe: boolean;
  }>;
  takeaways: string[];
  market_commentary: string;
  insights: string[];
  source: string;
}

export interface PortfolioState {
  capital: {
    initial: number;
    current: number;
    realized_pnl: number;
    unrealized_pnl: number;
    total_equity: number;
  };
  positions: Position[];
  exposure: ExposureData;
  intelligence: {
    regime: string;
    max_exposure_dynamic: number;
    portfolio_EV: number;
    capital_utilization: number;
    risk_clusters: number;
    cluster_detail: Record<string, number>;
  };
  summary: {
    open_positions: number;
    closed_trades: number;
    total_exposure_pct: number;
    available_capital_pct: number;
  };
}

export interface Position {
  trade_id: number;
  symbol: string;
  name: string;
  sector: string;
  entry_price: number;
  current_price: number;
  position_size: number;
  entry_value: number;
  current_value: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  stop_loss: number;
  target: number;
  mfe: number;
  mae: number;
  predicted_probability: number;
  predicted_ev?: number;
}

export interface ExposureData {
  capital: number;
  total_exposure: number;
  total_exposure_pct: number;
  capital_utilization: number;
  available_capital: number;
  positions_count: number;
  max_active_trades: number;
  max_total_exposure_pct: number;
  max_sector_exposure_pct: number;
  regime: string;
  sector_breakdown: Record<string, {
    symbols: string[];
    exposure: number;
    exposure_pct: number;
    unrealized_pnl: number;
  }>;
}

export interface PerformanceData {
  total_trades: number;
  open_trades: number;
  closed_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  total_pnl: number;
  initial_capital: number;
  current_capital: number;
  return_pct: number;
  max_drawdown: number;
  max_drawdown_pct: number;
  avg_mfe: number;
  avg_mae: number;
  best_trade: { symbol: string; pnl: number; pnl_pct: number; entry: number } | null;
  worst_trade: { symbol: string; pnl: number; pnl_pct: number; entry: number } | null;
  calibration: Record<string, { trades: number; predicted_avg: number; actual_win_rate: number }>;
  equity_curve: Array<{ timestamp: string | null; capital: number; trade_num: number }>;
}

export interface NewsItem {
  title: string;
  category: string;
  source: string;
  published: string;
  sentiment_score: number;
  impact: string;
}

export interface TradeRecord {
  id: number;
  symbol: string;
  entry_price: number;
  stop_loss: number;
  target_price: number;
  decision: string;
  timestamp: string;
  status: string;
  exit_price: number | null;
  exit_timestamp: string | null;
  outcome: string | null;
  pnl: number | null;
  pnl_pct: number | null;
  position_size: number;
  capital_at_entry: number;
  mfe: number;
  mae: number;
  predicted_probability: number;
  predicted_ev: number;
  actual_result: number | null;
  regime_at_entry: string;
  score_at_entry: number;
}

// ── Fetch Functions ────────────────────────────────────────────────

export const getScan = () => fetchAPI<ScanResult>("/scan");
export const getDecision = (symbol: string) => fetchAPI<TradeDecision>(`/decision?symbol=${symbol}`);
export const getMarketBrief = () => fetchAPI<MarketBrief>("/market-brief");
export const refreshInvestSmart = () => fetchAPI<{ status: string; data: InvestSmart }>("/invest-smart/refresh", { method: "POST" });
export const getPortfolio = () => fetchAPI<PortfolioState>("/portfolio");
export const getPortfolioPositions = () => fetchAPI<{ positions: Position[]; count: number; total_unrealized_pnl: number }>("/portfolio/positions");
export const getExposure = () => fetchAPI<ExposureData>("/portfolio/exposure");
export const getPerformance = () => fetchAPI<PerformanceData>("/performance");
export const getTrades = () => fetchAPI<{ trades: TradeRecord[]; count: number }>("/trades");
export const getNews = () => fetchAPI<{ articles: NewsItem[]; count: number }>("/news");

export interface ChartAnalysis {
  pattern: string;
  prediction: string;
  strength: number;
}

export const analyzeChart = async (file: File): Promise<{ status: string; data: ChartAnalysis }> => {
  const formData = new FormData();
  formData.append("file", file);
  
  const res = await fetch(`${API_BASE}/analyze-chart`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`API /analyze-chart: ${res.status}`);
  return res.json();
};

export interface StockDetails {
  symbol: string;
  name: string;
  sector: string;
  industry: string;
  description: string;
  current_price: number;
  market_cap: number;
  pe_ratio: string | number;
  dividend_yield: string | number;
  next_earnings_date: string;
  strengths: string[];
  weaknesses: string[];
  can_invest: string;
  risk_level: string;
  risk_analysis: string;
}

export const analyzeStockDetails = (symbol: string) => fetchAPI<StockDetails>(`/analyze-stock/${symbol}`);
