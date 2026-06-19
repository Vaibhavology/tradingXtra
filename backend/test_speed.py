"""Quick speed test for /api/scan and /api/decision endpoints."""
import requests
import time

BASE = "http://localhost:8000/api"

def test_scan():
    print("Testing /api/scan...")
    t = time.time()
    try:
        r = requests.get(f"{BASE}/scan", timeout=60)
        ms = int((time.time() - t) * 1000)
        d = r.json()
        total = d.get("total", 0)
        accepted = d.get("accepted", 0)
        loading = d.get("_loading", False)
        print(f"  Response: {ms}ms")
        print(f"  Total: {total} | Accepted: {accepted}")
        if loading:
            print(f"  Status: Still loading...")
        elif total > 0:
            for i, res in enumerate(d.get("results", [])[:3]):
                sym = res.get('symbol', '?')
                ev = res.get('ev', 0)
                prob = res.get('probability', 0)
                dec = res.get('decision', '?')
                print(f"  #{i+1} {sym:12s} EV={ev:>8.2f}  P(win)={prob:.0%}  {dec}")
    except Exception as e:
        print(f"  Error: {e}")

def test_decision(symbol="RELIANCE"):
    print(f"\nTesting /api/decision?symbol={symbol}...")
    t = time.time()
    try:
        r = requests.get(f"{BASE}/decision", params={"symbol": symbol}, timeout=30)
        ms = int((time.time() - t) * 1000)
        d = r.json()
        sym = d.get('symbol', '?')
        dec = d.get('decision', '?')
        ev = d.get('ev', 0)
        prob = d.get('probability', 0)
        print(f"  Response: {ms}ms")
        print(f"  {sym} -> {dec} | EV={ev:.2f} | P(win)={prob:.0%}")
    except Exception as e:
        print(f"  Error: {e}")

def test_status():
    print("Testing /api/status...")
    try:
        r = requests.get(f"{BASE}/status", timeout=10)
        d = r.json()
        batch = d.get("batch_evaluator", {})
        print(f"  Server: {d.get('server', '?')}")
        print(f"  Batch: running={batch.get('running', False)} | count={batch.get('last_count', 0)} | accepted={batch.get('last_accepted', 0)}")
    except Exception as e:
        print(f"  Error: {e}")

if __name__ == "__main__":
    test_status()
    print()

    print("=== FIRST CALL (may load from DB) ===")
    test_scan()

    print("\n=== SECOND CALL (should be memory cached) ===")
    test_scan()

    print("\n=== DECISION: First call ===")
    test_decision("RELIANCE")

    print("\n=== DECISION: Cached call ===")
    test_decision("RELIANCE")

    print("\n=== DECISION: Another stock ===")
    test_decision("COALINDIA")
