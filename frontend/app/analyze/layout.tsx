import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Stock Analyzer – Deep Dive Intelligence",
  description: "Analyze any NSE stock with AI-powered insights, real-time order book data, strengths, weaknesses, and investment verdicts.",
  alternates: {
    canonical: "/analyze",
  },
  openGraph: {
    title: "Stock Analyzer – TradingXtra",
    description: "Deep-dive AI analysis for any NSE stock with real-time order book data.",
    url: "/analyze",
  },
};

export default function AnalyzeLayout({ children }: { children: React.ReactNode }) {
  return children;
}
