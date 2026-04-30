import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Trade Analysis",
  description: "Detailed AI-powered trade analysis with decision scoring, agent analysis, price levels, and risk metrics.",
  alternates: {
    canonical: "/trade",
  },
  robots: {
    index: false,  // Dynamic pages — don't index individual trade URLs
    follow: true,
  },
};

export default function TradeLayout({ children }: { children: React.ReactNode }) {
  return children;
}
