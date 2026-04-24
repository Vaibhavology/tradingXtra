import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "TradingXtra — Intelligent Quantitative Trading Terminal",
  description: "An institutional-grade trading terminal featuring real-time market data, AI-driven stock intelligence, and expected value (EV) risk management.",
  keywords: ["quantitative trading", "stock market", "NIFTY50", "trading terminal", "AI trading", "algorithmic trading", "portfolio management", "expected value"],
  authors: [{ name: "Vaibhav" }],
  creator: "Vaibhav",
  publisher: "TradingXtra",
  openGraph: {
    title: "TradingXtra — Intelligent Quantitative Trading Terminal",
    description: "An institutional-grade trading terminal featuring real-time market data, AI-driven stock intelligence, and expected value (EV) risk management.",
    url: "https://tradingxtra.vercel.app",
    siteName: "TradingXtra",
    images: [
      {
        url: "https://tradingxtra.vercel.app/og-image.png",
        width: 1200,
        height: 630,
        alt: "TradingXtra Command Center Dashboard",
      },
    ],
    locale: "en_US",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "TradingXtra — Intelligent Quantitative Terminal",
    description: "AI-driven stock intelligence, automated EV risk management, and real-time market narratives.",
    images: ["https://tradingxtra.vercel.app/og-image.png"],
    creator: "@vaibhavology",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased min-h-screen">
        <Navbar />
        <main className="max-w-[1400px] mx-auto px-4 py-6">
          {children}
        </main>
      </body>
    </html>
  );
}
