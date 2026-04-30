import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Trade Journal – Complete Trade History",
  description: "Full trade log with entry/exit prices, P&L, win/loss outcomes, and market regime tracking for every AI-generated trade.",
  alternates: {
    canonical: "/trades",
  },
  openGraph: {
    title: "Trade Journal – TradingXtra",
    description: "Complete trade history with outcomes, P&L, and regime tracking.",
    url: "/trades",
  },
};

export default function TradesLayout({ children }: { children: React.ReactNode }) {
  return children;
}
