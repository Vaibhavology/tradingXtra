import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Portfolio – Live Position Tracking",
  description: "Track AI-generated paper trading positions in real-time with P&L, exposure analysis, and sector breakdowns.",
  alternates: {
    canonical: "/portfolio",
  },
  openGraph: {
    title: "Portfolio – TradingXtra",
    description: "Real-time paper trading portfolio with live P&L and risk exposure.",
    url: "/portfolio",
  },
};

export default function PortfolioLayout({ children }: { children: React.ReactNode }) {
  return children;
}
