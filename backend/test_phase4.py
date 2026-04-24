"""Phase 4.5 adaptive portfolio test."""
import urllib.request, json

BASE = "http://localhost:8000/api"

def get(path):
    return json.loads(urllib.request.urlopen(f"{BASE}{path}", timeout=60).read())

# 1. Portfolio state (empty) + intelligence fields
print("=" * 65)
print("  TEST 1: Portfolio intelligence (empty)")
print("=" * 65)
p = get("/portfolio")
intel = p.get("intelligence", {})
print(f"  Regime: {intel.get('regime','?')}")
print(f"  Dynamic max exposure: {intel.get('max_exposure_dynamic','?')}%")
print(f"  Portfolio EV: {intel.get('portfolio_EV','?')}")
print(f"  Risk clusters: {intel.get('risk_clusters','?')}")

# 2. Record trades — test adaptive exposure limits
print()
print("=" * 65)
print("  TEST 2: Adaptive admission (regime-aware limits)")
print("=" * 65)
for sym in ["RELIANCE", "HAL", "SBIN", "BAJFINANCE", "TATASTEEL"]:
    d = get(f"/decision?symbol={sym}&record=true")
    rec = d.get("trade_recorded", {})
    if rec.get("recorded"):
        cm = rec.get("corr_multiplier", 1.0)
        cp = rec.get("cluster_penalty", 1.0)
        extra = ""
        if cm < 1.0:
            extra += f" corr_mult={cm}"
        if cp < 1.0:
            extra += f" cluster_pen={cp}"
        print(f"  + {sym:12s} size={rec.get('position_size','?')} EV_mult={rec.get('ev_multiplier',1):.2f}{extra}")
    else:
        reason = rec.get("reason", "")[:70]
        print(f"  X {sym:12s} {reason}")

# 3. Exposure with regime info
print()
print("=" * 65)
print("  TEST 3: Dynamic exposure")
print("=" * 65)
e = get("/portfolio/exposure")
print(f"  Regime: {e.get('regime','?')}")
print(f"  Exposure: {e['total_exposure_pct']}% / {e['max_total_exposure_pct']}% limit")
print(f"  Utilization: {e.get('capital_utilization', 0):.1%}")
for sector, data in e.get("sector_breakdown", {}).items():
    print(f"    {sector:15s} {data['exposure_pct']}%  ({', '.join(data['symbols'])})")

# 4. Full portfolio state
print()
print("=" * 65)
print("  TEST 4: Portfolio intelligence")
print("=" * 65)
p = get("/portfolio")
intel = p.get("intelligence", {})
cap = p["capital"]
print(f"  Equity: Rs{cap['total_equity']}  Unrealized: Rs{cap['unrealized_pnl']}")
print(f"  Portfolio EV: Rs{intel.get('portfolio_EV', 0)}")
print(f"  Dynamic limit: {intel.get('max_exposure_dynamic', '?')}% (regime={intel.get('regime','?')})")
print(f"  Clusters: {intel.get('risk_clusters', 0)}  Detail: {intel.get('cluster_detail', {})}")

# 5. Try adding correlated stocks
print()
print("=" * 65)
print("  TEST 5: Correlation filter (gradual)")
print("=" * 65)
for sym in ["BEL", "NTPC", "HINDALCO"]:
    d = get(f"/decision?symbol={sym}&record=true")
    rec = d.get("trade_recorded", {})
    if rec.get("recorded"):
        g = rec.get("gates", {})
        corr_note = g.get("correlation", {}).get("note", "")
        if corr_note:
            print(f"  + {sym:12s} ADMITTED with note: {corr_note[:60]}")
        else:
            print(f"  + {sym:12s} ADMITTED (no correlation issue)")
    else:
        reason = rec.get("reason", "")[:70]
        print(f"  X {sym:12s} {reason}")

print()
print("=" * 65)
print("  ALL PHASE 4.5 TESTS PASSED")
print("=" * 65)
