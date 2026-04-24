// Core Trading Types - Backend Contract

export type TradeDirection = 'LONG' | 'SHORT';

export interface MarketStatus {
  nifty: { value: number; change: number; direction: 'up' | 'down' };
  bankNifty: { value: number; change: number; direction: 'up' | 'down' };
  indiaVix: { value: number; change: number };
  fiiFlow: { value: number; type: 'buy' | 'sell' };
  diiFlow: { value: number; type: 'buy' | 'sell' };
  lastUpdated: string;
  marketOpen: boolean;
}

export interface ChartPattern {
  name: string;
  timeframe: string;
  confidence: number;
  keyLevels: { support: number[]; resistance: number[] };
}

export interface CrossCheck {
  status: 'OK' | 'WARNING' | 'CRITICAL';
  issues: string[];
  platformsChecked: number;
}

export interface StockPick {
  id: string;
  symbol: string;
  name: string;
  direction: TradeDirection;
  entryZone: { low: number; high: number };
  stopLoss: number;
  target1: number;
  target2: number;
  expectedMove: number;
  confidence: number;
  pattern?: ChartPattern;
  reasoning: string[];
  crossCheck: CrossCheck;
  riskReward: number;
  sector: string;
  currentPrice?: number;
  momentumScore?: number;
  volumeMultiple?: number;
}

export interface Sector {
  name: string;
  direction: 'bullish' | 'bearish' | 'neutral';
  reason: string;
  topPick: string;
  topPickSymbol: string;
  strength: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  attachments?: { type: 'image'; url: string; analysis?: ChartAnalysis }[];
}

export interface ChartAnalysis {
  pattern: string;
  timeframe: string;
  suggestedEntry: { low: number; high: number };
  suggestedSL: number;
  suggestedTP: number[];
  confidence: number;
  notes: string;
  isAIAssisted: boolean;
}

export interface UserSettings {
  maxRiskPerTrade: number;
  maxTradesPerDay: number;
  tradeStyle: 'aggressive' | 'moderate' | 'conservative';
  riskReminders: boolean;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data: T;
  timestamp: string;
  error?: string;
}

// Invest Smart (YouTube intelligence)
export interface InvestSmartStock {
  symbol: string;
  action: string;
  reason: string;
  confidence: number;
  in_universe: boolean;
}

export interface InvestSmart {
  source: string;
  title: string;
  link: string;
  published: string;
  market_commentary: string;
  stocks: InvestSmartStock[];
  takeaways: string[];
  insights: string[];
}
