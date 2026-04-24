'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, MessageSquare, PieChart, Search, Settings, Activity } from 'lucide-react';

const navItems = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/chat', label: 'Chat', icon: MessageSquare },
  { href: '/sectors', label: 'Sectors', icon: PieChart },
  { href: '/scanner', label: 'Scanner', icon: Search },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-terminal-card border-b border-terminal-border">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <Activity className="w-6 h-6 text-terminal-accent" />
            <span className="font-semibold text-lg tracking-tight">TradingXtra</span>
            <span className="text-xs text-terminal-muted ml-2 hidden sm:block">Research Terminal</span>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm transition-colors ${
                    isActive
                      ? 'bg-terminal-accent/10 text-terminal-accent'
                      : 'text-terminal-muted hover:text-terminal-text hover:bg-terminal-border/50'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden md:block">{item.label}</span>
                </Link>
              );
            })}
          </div>

          {/* Status Indicator */}
          <div className="flex items-center gap-2">
            <div className="status-dot bg-terminal-success" />
            <span className="text-xs text-terminal-muted hidden sm:block">Live</span>
          </div>
        </div>
      </div>
    </nav>
  );
}
