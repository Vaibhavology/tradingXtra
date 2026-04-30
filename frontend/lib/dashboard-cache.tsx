"use client";
import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import {
  getScan, getMarketBrief, getPortfolio, getPerformance, wakeBackend,
  ScanResult, MarketBrief as MarketBriefType, PortfolioState, PerformanceData,
} from "@/lib/api";

// ── Types ──────────────────────────────────────────────────────────

interface DashboardCache {
  scan: ScanResult | null;
  brief: MarketBriefType | null;
  portfolio: PortfolioState | null;
  perf: PerformanceData | null;
  loading: boolean;
  scanLoading: boolean;
  error: string | null;
  lastFetched: number; // timestamp ms
  lastScanFetched: number;
}

interface DashboardContextValue extends DashboardCache {
  /** Update brief (e.g., after invest-smart refresh) */
  setBrief: React.Dispatch<React.SetStateAction<MarketBriefType | null>>;
  /** Force a full refetch */
  forceRefresh: () => void;
}

const CACHE_KEY = "tradingxtra_dashboard_cache";
const CACHE_TTL = 3 * 60 * 1000; // 3 minutes — don't re-fetch if data is fresh
const SCAN_STAGGER_DELAY = 3000; // ms delay before starting scan load

// ── Helpers ────────────────────────────────────────────────────────

function loadFromStorage(): Partial<DashboardCache> | null {
  try {
    const raw = sessionStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveToStorage(cache: DashboardCache) {
  try {
    // Don't persist loading/error states
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({
      scan: cache.scan,
      brief: cache.brief,
      portfolio: cache.portfolio,
      perf: cache.perf,
      lastFetched: cache.lastFetched,
      lastScanFetched: cache.lastScanFetched,
    }));
  } catch {
    // sessionStorage full or unavailable — ignore
  }
}

// ── Context ────────────────────────────────────────────────────────

const DashboardContext = createContext<DashboardContextValue | null>(null);

export function useDashboard(): DashboardContextValue {
  const ctx = useContext(DashboardContext);
  if (!ctx) throw new Error("useDashboard must be inside DashboardCacheProvider");
  return ctx;
}

export function DashboardCacheProvider({ children }: { children: React.ReactNode }) {
  // Initialize from sessionStorage if available
  const cached = useRef(loadFromStorage());

  const [scan, setScan] = useState<ScanResult | null>(cached.current?.scan ?? null);
  const [brief, setBrief] = useState<MarketBriefType | null>(cached.current?.brief ?? null);
  const [portfolio, setPortfolio] = useState<PortfolioState | null>(cached.current?.portfolio ?? null);
  const [perf, setPerf] = useState<PerformanceData | null>(cached.current?.perf ?? null);
  const [loading, setLoading] = useState(!cached.current?.brief); // not loading if we have cached brief
  const [scanLoading, setScanLoading] = useState(!cached.current?.scan);
  const [error, setError] = useState<string | null>(null);
  const [lastFetched, setLastFetched] = useState(cached.current?.lastFetched ?? 0);
  const [lastScanFetched, setLastScanFetched] = useState(cached.current?.lastScanFetched ?? 0);

  const fetchingRef = useRef(false);

  // ── Core fetch logic ──
  const loadFast = useCallback(async (isCancelled: { current: boolean }) => {
    try {
      const [b, p, pf] = await Promise.allSettled([
        getMarketBrief(), getPortfolio(), getPerformance(),
      ]);
      if (isCancelled.current) return;
      if (b.status === "fulfilled") setBrief(b.value);
      if (p.status === "fulfilled") setPortfolio(p.value);
      if (pf.status === "fulfilled") setPerf(pf.value);
      setLastFetched(Date.now());
    } catch (e) {
      console.error("Fast load error:", e);
    } finally {
      if (!isCancelled.current) setLoading(false);
    }
  }, []);

  const loadScan = useCallback(async (isCancelled: { current: boolean }) => {
    try {
      const s = await getScan();
      if (!isCancelled.current) {
        setScan(s);
        setLastScanFetched(Date.now());
      }
    } catch (e) {
      console.error("Scan load error:", e);
    } finally {
      if (!isCancelled.current) setScanLoading(false);
    }
  }, []);

  const startFetching = useCallback((force = false) => {
    if (fetchingRef.current && !force) return;
    fetchingRef.current = true;

    const isCancelled = { current: false };

    const now = Date.now();
    const fastStale = force || (now - lastFetched > CACHE_TTL);
    const scanStale = force || (now - lastScanFetched > CACHE_TTL);

    // If data is not stale, skip re-fetching
    if (!fastStale && !scanStale) {
      setLoading(false);
      setScanLoading(false);
      fetchingRef.current = false;
      return;
    }

    // Wake backend
    wakeBackend();

    if (fastStale) {
      setLoading(brief === null); // only show loading if we have no cached data
      loadFast(isCancelled);
    } else {
      setLoading(false);
    }

    let scanTimeout: ReturnType<typeof setTimeout> | null = null;
    if (scanStale) {
      setScanLoading(scan === null); // only show loading if we have no cached data
      scanTimeout = setTimeout(() => loadScan(isCancelled), SCAN_STAGGER_DELAY);
    } else {
      setScanLoading(false);
    }

    // Set up the 3 minute periodic refresh
    const interval = setInterval(() => {
      loadFast(isCancelled);
      loadScan(isCancelled);
    }, 180_000);

    // This is a long-lived effect — it cleans up when the provider unmounts (never in practice)
    // But we store cleanup in ref for forceRefresh
    cleanupRef.current = () => {
      isCancelled.current = true;
      if (scanTimeout) clearTimeout(scanTimeout);
      clearInterval(interval);
      fetchingRef.current = false;
    };
  }, [lastFetched, lastScanFetched, brief, scan, loadFast, loadScan]);

  const cleanupRef = useRef<(() => void) | null>(null);

  // ── Initial mount — fetch once ──
  useEffect(() => {
    startFetching();
    return () => {
      if (cleanupRef.current) cleanupRef.current();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Persist to sessionStorage on data changes ──
  useEffect(() => {
    saveToStorage({ scan, brief, portfolio, perf, loading, scanLoading, error, lastFetched, lastScanFetched });
  }, [scan, brief, portfolio, perf, lastFetched, lastScanFetched, loading, scanLoading, error]);

  // ── Force refresh ──
  const forceRefresh = useCallback(() => {
    if (cleanupRef.current) cleanupRef.current();
    setLastFetched(0);
    setLastScanFetched(0);
    setScanLoading(true);
    setLoading(true);

    // We need to refetch immediately
    fetchingRef.current = false;
    const isCancelled = { current: false };
    wakeBackend();
    loadFast(isCancelled);
    const scanTimeout = setTimeout(() => loadScan(isCancelled), SCAN_STAGGER_DELAY);
    const interval = setInterval(() => {
      loadFast(isCancelled);
      loadScan(isCancelled);
    }, 180_000);
    cleanupRef.current = () => {
      isCancelled.current = true;
      clearTimeout(scanTimeout);
      clearInterval(interval);
      fetchingRef.current = false;
    };
  }, [loadFast, loadScan]);

  return (
    <DashboardContext.Provider value={{
      scan, brief, portfolio, perf,
      loading, scanLoading, error,
      lastFetched, lastScanFetched,
      setBrief, forceRefresh,
    }}>
      {children}
    </DashboardContext.Provider>
  );
}
