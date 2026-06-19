"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Zap, Search, Folder, TrendingUp, ClipboardList, User } from "lucide-react";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: <Zap className="w-3.5 h-3.5" /> },
  { href: "/analyze", label: "Analyze", icon: <Search className="w-3.5 h-3.5" /> },
  { href: "/portfolio", label: "Portfolio", icon: <Folder className="w-3.5 h-3.5" /> },
  { href: "/performance", label: "Performance", icon: <TrendingUp className="w-3.5 h-3.5" /> },
  { href: "/trades", label: "Trades", icon: <ClipboardList className="w-3.5 h-3.5" /> },
  { href: "/about", label: "About", icon: <User className="w-3.5 h-3.5" /> },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--border-default)] bg-[var(--bg-primary)]/95 backdrop-blur-sm">
      <div className="max-w-[1440px] mx-auto px-4 h-12 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <span className="text-base font-semibold tracking-tight text-[var(--text-primary)]">
            TradingXtra
          </span>
        </Link>

        <div className="flex items-center gap-0.5 overflow-x-auto" style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}>
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`px-2.5 py-1 rounded text-[13px] font-medium transition-colors shrink-0 flex items-center gap-1.5 ${
                  active
                    ? "text-[var(--text-primary)] bg-[var(--bg-surface)]"
                    : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
