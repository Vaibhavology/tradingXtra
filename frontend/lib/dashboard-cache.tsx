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
    // Trim scan results for storage — keep max 50 to avoid mobile sessionStorage overflow
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
    sessionStorage.setItem(CACHE_KEY, JSON.stringify({
      scan: trimmedScan,
      brief: cache.brief,
      portfolio: cache.portfolio,
      perf: cache.perf,
      lastFetched: cache.lastFetched,
      lastScanFetched: cache.lastScanFetched,
    }));
  } catch {
    // sessionStorage full or unavailable — clear and retry with minimal data
    try {
      sessionStorage.removeItem(CACHE_KEY);
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
  // sessionStorage is only available on the client, so we defer reading it
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
  const hydratedRef = useRef(false);

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

  const scanRetryRef = useRef(0);
  const MAX_SCAN_RETRIES = 3;
  const SCAN_RETRY_DELAY = 10_000; // 10 seconds

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
      scanRetryRef.current = 0; // Reset retries for periodic refresh
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

  // ── Hydrate from sessionStorage + start fetching (client-only, single mount) ──
  useEffect(() => {
    const cached = loadFromStorage();
    if (cached) {
      if (cached.scan) setScan(cached.scan as ScanResult);
      if (cached.brief) setBrief(cached.brief as MarketBriefType);
      if (cached.portfolio) setPortfolio(cached.portfolio as PortfolioState);
      if (cached.perf) setPerf(cached.perf as PerformanceData);
      if (cached.lastFetched) setLastFetched(cached.lastFetched);
      if (cached.lastScanFetched) setLastScanFetched(cached.lastScanFetched);
      // If we have cached brief, don't show full loading skeleton
      if (cached.brief) setLoading(false);
      if (cached.scan) setScanLoading(false);
    }

    // Start background fetch/refresh (startFetching uses stale closure values,
    // but that's fine — it will treat data as stale and re-validate in background).
    // We call it directly here rather than via startFetching() to avoid the closure
    // overriding the loading states we just set above.
    const isCancelled = { current: false };
    wakeBackend();
    loadFast(isCancelled);
    const scanTimeout = setTimeout(() => loadScan(isCancelled), SCAN_STAGGER_DELAY);
    const interval = setInterval(() => {
      loadFast(isCancelled);
      scanRetryRef.current = 0;
      loadScan(isCancelled);
    }, 180_000);

    cleanupRef.current = () => {
      isCancelled.current = true;
      clearTimeout(scanTimeout);
      clearInterval(interval);
      fetchingRef.current = false;
    };

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
    scanRetryRef.current = 0; // Reset retries on force refresh
    const isCancelled = { current: false };
    wakeBackend();
    loadFast(isCancelled);
    const scanTimeout = setTimeout(() => loadScan(isCancelled), SCAN_STAGGER_DELAY);
    const interval = setInterval(() => {
      loadFast(isCancelled);
      scanRetryRef.current = 0;
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
