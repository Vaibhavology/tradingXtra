import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Performance – Trading System Metrics",
  description: "Track win rates, profit factor, equity curves, drawdowns, and calibration data for the AI trading system.",
  alternates: {
    canonical: "/performance",
  },
  openGraph: {
    title: "Performance – TradingXtra",
    description: "Detailed performance analytics and equity curves for the AI trading engine.",
    url: "/performance",
  },
};

export default function PerformanceLayout({ children }: { children: React.ReactNode }) {
  return children;
}
