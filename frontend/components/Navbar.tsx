"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "⚡" },
  { href: "/analyze", label: "Analyze", icon: "🔍" },
  { href: "/portfolio", label: "Portfolio", icon: "📂" },
  { href: "/performance", label: "Performance", icon: "📈" },
  { href: "/trades", label: "Trades", icon: "📋" },
  { href: "/about", label: "About", icon: "👤" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--border-default)] bg-[var(--bg-secondary)]/95 backdrop-blur-sm">
      <div className="max-w-[1400px] mx-auto px-4 min-h-14 flex flex-col sm:flex-row items-center justify-between gap-2 py-2 sm:py-0">
        <div className="w-full sm:w-auto flex justify-center sm:justify-start">
          <Link href="/" className="flex items-center gap-2 group shrink-0">
            <span className="text-xl">🔥</span>
            <span className="text-lg font-bold tracking-tight text-white group-hover:text-[var(--accent-blue)] transition-colors">
              TradingXtra
            </span>
            <span className="text-[10px] font-mono bg-[var(--accent-blue)]/15 text-[var(--accent-blue)] px-1.5 py-0.5 rounded">
              v5
            </span>
          </Link>
        </div>

        <div className="flex items-center gap-1 w-full sm:w-auto overflow-x-auto justify-start sm:justify-end pb-1 sm:pb-0" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors shrink-0 flex items-center ${
                  active
                    ? "bg-[var(--accent-blue)]/15 text-[var(--accent-blue)]"
                    : "text-[var(--text-secondary)] hover:text-white hover:bg-[var(--bg-card)]"
                }`}
              >
                <span className="text-lg md:text-sm md:mr-1.5">{item.icon}</span>
                <span className="ml-1.5 md:ml-0 inline-block">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
