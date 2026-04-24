"""Phase 2.5 integration test."""
import urllib.request, json, time

BASE = "http://localhost:8000/api"

def get(path):
    return json.loads(urllib.request.urlopen(f"{BASE}{path}", timeout=30).read())

print("=" * 65)
print("  TEST 1: Decision (RELIANCE) — with agents + sentiment + regime")
print("=" * 65)
t = time.time()
d = get("/decision?symbol=RELIANCE")
ms = (time.time() - t) * 1000
print(f"  {d['decision']} in {ms:.0f}ms")
print(f"  Score={d['score']}  P(win)={d['probability']:.2%}  EV=Rs{d['ev']}")
print(f"  Regime: {d['regime']}  Bias: {d.get('market_bias','N/A')}")
print(f"  Features: {d['features']}")
print(f"  Agents:")
for k, v in d.get('agents', {}).items():
    print(f"    {k}: {v}")
print(f"  Reasoning:")
for r in d.get('reasoning', []):
    print(f"    - {r}")

print()
print("=" * 65)
print("  TEST 2: Market Brief")
print("=" * 65)
t = time.time()
b = get("/market-brief")
ms = (time.time() - t) * 1000
print(f"  [{ms:.0f}ms] Bias={b['bias']} Behavior={b['behavior']}")
print(f"  NIFTY 5d: {b.get('nifty_return_5d','?')}%  VIX: {b.get('vix','?')}")
for g in b.get('guidance', []):
    print(f"    > {g}")

print()
print("=" * 65)
print("  TEST 3: Speed — 5 cached stocks")
print("=" * 65)
for sym in ["HAL", "SBIN", "TATASTEEL", "INFY", "BAJFINANCE"]:
    t = time.time()
    d = get(f"/decision?symbol={sym}")
    ms = (time.time() - t) * 1000
    print(f"  {sym:12s} {d['decision']:6s}  P={d['probability']:.2%}  EV=Rs{d['ev']:>7.2f}  SE={d['features'].get('SE',0):.2f}  [{ms:.0f}ms]")

print()
print("=" * 65)
print("  ALL TESTS PASSED")
print("=" * 65)
