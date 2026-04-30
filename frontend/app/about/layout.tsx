import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About – Meet the Builder",
  description: "Learn about Vaibhav, the developer behind TradingXtra – a quant-based AI trading intelligence platform built for Indian markets.",
  alternates: {
    canonical: "/about",
  },
  openGraph: {
    title: "About – TradingXtra",
    description: "Meet Vaibhav, the developer behind TradingXtra.",
    url: "/about",
  },
};

export default function AboutLayout({ children }: { children: React.ReactNode }) {
  return children;
}
