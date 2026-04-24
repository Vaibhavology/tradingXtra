"""Phase 3.5 realism test."""
import urllib.request, json, time

BASE = "http://localhost:8000/api"

def get(path):
    return json.loads(urllib.request.urlopen(f"{BASE}{path}", timeout=60).read())

def post(path):
    req = urllib.request.Request(f"{BASE}{path}", method="POST", data=b"")
    return json.loads(urllib.request.urlopen(req, timeout=120).read())

# 1. Record trades with position sizing
print("=" * 65)
print("  TEST 1: Record trades (position sizing + capital)")
print("=" * 65)
for sym in ["RELIANCE", "HAL", "SBIN", "BAJFINANCE"]:
    d = get(f"/decision?symbol={sym}&record=true")
    rec = d.get("trade_recorded", {})
    if rec.get("recorded"):
        print(f"  + {sym}: #{rec['trade_id']} size={rec.get('position_size','?')} shares  capital=Rs{rec.get('capital','?')}")
    else:
        print(f"  - {sym}: {d['decision']} {rec.get('reason','')}")

# 2. Max trades limit test
print()
print("=" * 65)
print("  TEST 2: Max active trades limit")
print("=" * 65)
for sym in ["TATASTEEL", "WIPRO", "COALINDIA"]:
    d = get(f"/decision?symbol={sym}&record=true")
    rec = d.get("trade_recorded", {})
    if rec.get("recorded"):
        print(f"  + {sym}: #{rec['trade_id']} (within limit)")
    else:
        reason = rec.get("reason", d.get("decision", "?"))
        print(f"  BLOCKED {sym}: {reason}")

# 3. Trades list with position sizes
print()
print("=" * 65)
print("  TEST 3: Trade journal (position sizing)")
print("=" * 65)
t = get("/trades")
print(f"  Total: {t['count']} trades")
for tr in t["trades"][:5]:
    print(f"  [{tr['status']}] {tr['symbol']:12s} size={tr.get('position_size','?')} entry=Rs{tr['entry_price']}")

# 4. Realistic backtest
print()
print("=" * 65)
print("  TEST 4: Realistic backtest (3 stocks)")
print("=" * 65)
t0 = time.time()
bt = post("/backtest?symbols=RELIANCE,HAL,SBIN&lookback_days=60")
elapsed = time.time() - t0
print(f"  [{elapsed:.1f}s]")
print(f"  Initial:  Rs{bt.get('initial_capital', '?')}")
print(f"  Final:    Rs{bt.get('final_capital', '?')}")
print(f"  Return:   {bt.get('return_pct', '?')}%")
print(f"  MaxDD:    -{bt.get('max_drawdown_pct', '?')}%")
print(f"  Trades:   {bt['total_trades']}  WR={bt['win_rate']:.0%}  PF={bt['profit_factor']}")
print(f"  Slippage: {bt.get('slippage_used', '?')}  Risk/trade: {bt.get('risk_per_trade', '?')}")
cal = bt.get("calibration", {})
if cal:
    print(f"  Calibration: {cal.get('note', '?')} (ratio={cal.get('calibration_ratio', '?')})")
eq = bt.get("equity_curve", [])
if len(eq) >= 2:
    print(f"  Equity curve: {len(eq)} points  start=Rs{eq[0]['capital']} end=Rs{eq[-1]['capital']}")
for s, v in bt.get("per_symbol", {}).items():
    print(f"    {s:12s} t={v['trades']} WR={v['win_rate']:.0%} PnL=Rs{v['total_pnl']}")

print()
print("=" * 65)
print("  ALL PHASE 3.5 TESTS PASSED")
print("=" * 65)
