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
const REFRESH_INTERVAL = 180_000; // 3 minutes periodic refresh

// ── Helpers ────────────────────────────────────────────────────────

function loadFromStorage(): Partial<DashboardCache> | null {
  try {
    // Use localStorage so data persists across tab/browser closes
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function saveToStorage(cache: DashboardCache) {
  try {
    // Trim scan results for storage — keep max 50 to avoid overflow
    const trimmedScan = cache.scan ? {
      ...cache.scan,
      results: cache.scan.results.slice(0, 50).map(r => ({
        symbol: r.symbol, name: r.name, sector: r.sector,
        score: r.score, probability: r.probability, ev: r.ev,
        entry: r.entry, stop_loss: r.stop_loss, target: r.target,
        atr: r.atr, decision: r.decision, rejection_reason: r.rejection_reason,
        reward_risk: r.reward_risk, regime: r.regime,
      })),
    } : null;

    // Don't persist loading/error states
    localStorage.setItem(CACHE_KEY, JSON.stringify({
      scan: trimmedScan,
      brief: cache.brief,
      portfolio: cache.portfolio,
      perf: cache.perf,
      lastFetched: cache.lastFetched,
      lastScanFetched: cache.lastScanFetched,
    }));
  } catch {
    // localStorage full or unavailable — clear and retry
    try {
      localStorage.removeItem(CACHE_KEY);
    } catch {
      // ignore — truly unavailable
    }
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
  // Always start with loading=true and null data to avoid hydration mismatch.
  // localStorage is only available on the client, so we defer reading it
  // to a useEffect below. This guarantees server and client render the same
  // initial HTML (the loading skeleton).
  const [scan, setScan] = useState<ScanResult | null>(null);
  const [brief, setBrief] = useState<MarketBriefType | null>(null);
  const [portfolio, setPortfolio] = useState<PortfolioState | null>(null);
  const [perf, setPerf] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [scanLoading, setScanLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastFetched, setLastFetched] = useState(0);
  const [lastScanFetched, setLastScanFetched] = useState(0);

  const fetchingRef = useRef(false);

  // ── Core fetch logic ──
  const fastRetryRef = useRef(0);
  const MAX_FAST_RETRIES = 6;
  const FAST_RETRY_DELAY = 15_000; // 15 seconds

  const loadFast = useCallback(async (isCancelled: { current: boolean }) => {
    try {
      const [b, p, pf] = await Promise.allSettled([
        getMarketBrief(), getPortfolio(), getPerformance(),
      ]);
      if (isCancelled.current) return;
      const gotBrief = b.status === "fulfilled";
      if (gotBrief) setBrief(b.value);
      if (p.status === "fulfilled") setPortfolio(p.value);
      if (pf.status === "fulfilled") setPerf(pf.value);
      if (gotBrief) {
        setLastFetched(Date.now());
        fastRetryRef.current = 0; // Reset on success
      } else if (fastRetryRef.current < MAX_FAST_RETRIES) {
        // Brief failed — schedule a fast retry (backend might still be starting)
        fastRetryRef.current += 1;
        console.warn(`Fast load retry ${fastRetryRef.current}/${MAX_FAST_RETRIES} in ${FAST_RETRY_DELAY/1000}s`);
        setTimeout(() => {
          if (!isCancelled.current) loadFast(isCancelled);
        }, FAST_RETRY_DELAY);
      }
    } catch (e) {
      console.error("Fast load error:", e);
      // Network-level failure — retry if we haven't exhausted
      if (!isCancelled.current && fastRetryRef.current < MAX_FAST_RETRIES) {
        fastRetryRef.current += 1;
        console.warn(`Fast load retry ${fastRetryRef.current}/${MAX_FAST_RETRIES} in ${FAST_RETRY_DELAY/1000}s`);
        setTimeout(() => {
          if (!isCancelled.current) loadFast(isCancelled);
        }, FAST_RETRY_DELAY);
      }
    } finally {
      if (!isCancelled.current) setLoading(false);
    }
  }, []);

  const scanRetryRef = useRef(0);
  const MAX_SCAN_RETRIES = 6;
  const SCAN_RETRY_DELAY = 15_000; // 15 seconds

  const loadScan = useCallback(async (isCancelled: { current: boolean }) => {
    try {
      const s = await getScan();
      if (!isCancelled.current) {
        setScan(s);
        setLastScanFetched(Date.now());
        scanRetryRef.current = 0; // Reset retry counter on success
      }
    } catch (e) {
      console.error("Scan load error:", e);
      // Auto-retry if we haven't exhausted retries
      if (!isCancelled.current && scanRetryRef.current < MAX_SCAN_RETRIES) {
        scanRetryRef.current += 1;
        console.warn(`Scan auto-retry ${scanRetryRef.current}/${MAX_SCAN_RETRIES} in ${SCAN_RETRY_DELAY/1000}s`);
        setTimeout(() => {
          if (!isCancelled.current) loadScan(isCancelled);
        }, SCAN_RETRY_DELAY);
        return; // Don't clear scanLoading yet — still retrying
      }
    } finally {
      // Only clear loading if we're not retrying
      if (!isCancelled.current && scanRetryRef.current >= MAX_SCAN_RETRIES) {
        setScanLoading(false);
      } else if (!isCancelled.current && scanRetryRef.current === 0) {
        setScanLoading(false);
      }
    }
  }, []);

  const cleanupRef = useRef<(() => void) | null>(null);

  // ── Hydrate from localStorage + conditionally fetch (client-only, single mount) ──
  useEffect(() => {
    const cached = loadFromStorage();
    const now = Date.now();
    let cachedLastFetched = 0;
    let cachedLastScanFetched = 0;
    let hasBrief = false;
    let hasScan = false;

    if (cached) {
      if (cached.scan) { setScan(cached.scan as ScanResult); hasScan = true; }
      if (cached.brief) { setBrief(cached.brief as MarketBriefType); hasBrief = true; }
      if (cached.portfolio) setPortfolio(cached.portfolio as PortfolioState);
      if (cached.perf) setPerf(cached.perf as PerformanceData);
      if (cached.lastFetched) { setLastFetched(cached.lastFetched); cachedLastFetched = cached.lastFetched; }
      if (cached.lastScanFetched) { setLastScanFetched(cached.lastScanFetched); cachedLastScanFetched = cached.lastScanFetched; }
      // If we have cached data, don't show loading skeleton
      if (hasBrief) setLoading(false);
      if (hasScan) setScanLoading(false);
    }

    // Check staleness — only fetch if data is stale or missing
    const fastStale = !hasBrief || (now - cachedLastFetched > CACHE_TTL);
    const scanStale = !hasScan || (now - cachedLastScanFetched > CACHE_TTL);

    const isCancelled = { current: false };

    if (fastStale || scanStale) {
      wakeBackend();
    }

    // Only fetch fast data (brief/portfolio/perf) if stale or missing
    if (fastStale) {
      // Show loading skeleton only if we have nothing cached
      if (!hasBrief) setLoading(true);
      loadFast(isCancelled);
    } else {
      setLoading(false);
      console.log(`Dashboard: brief is fresh (${((now - cachedLastFetched)/1000).toFixed(0)}s old), skipping fetch`);
    }

    // Only fetch scan if stale or missing
    let scanTimeout: ReturnType<typeof setTimeout> | null = null;
    if (scanStale) {
      if (!hasScan) setScanLoading(true);
      scanTimeout = setTimeout(() => loadScan(isCancelled), SCAN_STAGGER_DELAY);
    } else {
      setScanLoading(false);
      console.log(`Dashboard: scan is fresh (${((now - cachedLastScanFetched)/1000).toFixed(0)}s old), skipping fetch`);
    }

    // Set up periodic refresh (every 3 minutes)
    const interval = setInterval(() => {
      fastRetryRef.current = 0;
      scanRetryRef.current = 0;
      loadFast(isCancelled);
      loadScan(isCancelled);
    }, REFRESH_INTERVAL);

    cleanupRef.current = () => {
      isCancelled.current = true;
      if (scanTimeout) clearTimeout(scanTimeout);
      clearInterval(interval);
      fetchingRef.current = false;
    };

    return () => {
      if (cleanupRef.current) cleanupRef.current();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Persist to localStorage on data changes ──
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
    fastRetryRef.current = 0;
    scanRetryRef.current = 0;
    const isCancelled = { current: false };
    wakeBackend();
    loadFast(isCancelled);
    const scanTimeout = setTimeout(() => loadScan(isCancelled), SCAN_STAGGER_DELAY);
    const interval = setInterval(() => {
      loadFast(isCancelled);
      scanRetryRef.current = 0;
      loadScan(isCancelled);
    }, REFRESH_INTERVAL);
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
