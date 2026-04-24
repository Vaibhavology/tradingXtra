import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  metadataBase: new URL("https://tradingxtra.vercel.app"),
  title: "TradingXtra – AI Trading Terminal",
  description: "Quant-based trading intelligence platform with EV scoring, market brief, AI-powered stock insights, and professional trading dashboard.",
  keywords: [
    "trading app", "stock analysis", "AI trading", "quant trading", "stock prediction India",
    "AI stock analysis", "trading signals", "stock market dashboard", "trading terminal",
    "algorithmic trading platform", "expected value trading", "probability based trading",
    "best trading app India", "how to analyze stocks", "how to trade stocks",
    "stock market strategies", "intraday trading strategies", "swing trading analysis",
    "NSE stocks analysis", "BSE stock market", "Indian stock market analysis", "Nifty 50 analysis", "bank nifty trading",
    "AI stock prediction", "machine learning trading", "AI trading assistant", "automated trading insights",
    "trading dashboard app", "professional trading software", "stock research platform",
    "market intelligence platform", "vaibhavology", "Vaibhav S"
  ],
  authors: [{ name: "Vaibhav S" }],
  creator: "Vaibhav S",
  publisher: "TradingXtra",
  openGraph: {
    title: "TradingXtra – AI Trading Terminal",
    description: "Quant-based trading intelligence platform with EV scoring, market brief, AI-powered stock insights, and professional trading dashboard.",
    url: "https://tradingxtra.vercel.app",
    siteName: "TradingXtra",
    images: [
      {
        url: "/og-image.png",
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
    title: "TradingXtra – AI Trading Terminal",
    description: "Quant-based trading intelligence platform with EV scoring, market brief, AI-powered stock insights, and professional trading dashboard.",
    images: ["/og-image.png"],
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
