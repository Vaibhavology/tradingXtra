"""Speed test: measure response time for all cached stocks."""
import urllib.request
import json
import time

BASE = "http://localhost:8000/api"

# Test 1: Single stock (should be instant from cache)
print("=" * 60)
print("  SPEED TEST — Cached Response Times")
print("=" * 60)

symbols = ["RELIANCE", "TCS", "TATASTEEL", "SBIN", "HDFCBANK",
           "HAL", "BEL", "BAJFINANCE", "INFY", "WIPRO"]

for sym in symbols:
    start = time.time()
    r = urllib.request.urlopen(f"{BASE}/decision?symbol={sym}")
    data = json.loads(r.read())
    ms = (time.time() - start) * 1000
    print(f"  {sym:12s} → {data['decision']:6s}  P={data['probability']:.2%}  EV=₹{data['ev']:>7.2f}  [{ms:.0f}ms]")

# Test 2: System status
print()
r = urllib.request.urlopen(f"{BASE}/status")
status = json.loads(r.read())
print(f"  Preload: {'COMPLETE' if status['preload']['complete'] else 'IN PROGRESS'}")
print(f"  Cache size: {status['preload']['cache_size']} symbols")
print(f"  DB rows: {status['database']['total_rows']}")

# Test 3: Full scan timing
print()
print("  Full /scan (35 stocks)...")
start = time.time()
r = urllib.request.urlopen(f"{BASE}/scan")
scan = json.loads(r.read())
ms = (time.time() - start) * 1000
print(f"  → {scan['accepted']} ACCEPTED, {scan['rejected']} REJECTED in {ms:.0f}ms")
print()
print("=" * 60)
