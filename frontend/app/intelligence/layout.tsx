import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Market Intelligence – Real-Time Regime Detection",
  description: "Advanced market intelligence with regime detection, global sentiment analysis, India VIX, risk alerts, and tactical trading guidance.",
  alternates: {
    canonical: "/intelligence",
  },
  openGraph: {
    title: "Market Intelligence – TradingXtra",
    description: "Real-time market regime detection and risk assessment for Indian markets.",
    url: "/intelligence",
  },
};

export default function IntelligenceLayout({ children }: { children: React.ReactNode }) {
  return children;
}
