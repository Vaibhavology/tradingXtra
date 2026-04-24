"""Test market-brief endpoint end-to-end."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests

print("Calling /api/market-brief (this takes ~30s for Gemini)...")
r = requests.get('http://localhost:8000/api/market-brief', timeout=120)
d = r.json()

print(f"\n{'='*60}")
print(f"Bias:      {d.get('bias')}")
print(f"Behavior:  {d.get('behavior')}")
print(f"VIX:       {d.get('vix')}")
print(f"Regime:    {d.get('regime', {}).get('regime', '?')}")
print(f"NIFTY 5d:  {d.get('nifty_return_5d')}%")
print(f"NIFTY 1d:  {d.get('nifty_return_1d')}%")

# Sectors
ss = d.get('sector_strength', {})
print(f"\nStrong sectors: {ss.get('strong', [])}")
print(f"Weak sectors:   {ss.get('weak', [])}")

# Risk alerts
print(f"\nRisk alerts:")
for a in d.get('risk_alerts', []):
    print(f"  ⚠ {a}")

# Guidance
print(f"\nGuidance:")
for g in d.get('guidance', []):
    print(f"  → {g}")

# Invest Smart
is_ = d.get('invest_smart')
print(f"\n{'='*60}")
print(f"INVEST SMART")
print(f"{'='*60}")
if is_:
    print(f"Title:       {is_.get('title','?')[:80]}")
    print(f"Link:        {is_.get('link','?')}")
    print(f"Source:      {is_.get('source','?')}")
    print(f"Stocks:      {len(is_.get('stocks',[]))}")
    print(f"Takeaways:   {len(is_.get('takeaways',[]))}")
    print(f"Commentary:  {is_.get('market_commentary','')[:120]}")
    
    if is_.get('stocks'):
        print(f"\n  Stocks analyzed:")
        for s in is_['stocks'][:8]:
            sym = s.get('symbol', '?')
            act = s.get('action', '?')
            reason = s.get('reason', '')[:60]
            conf = s.get('confidence', 0)
            print(f"    {act:6s} {sym:12s} ({conf:.0%}) — {reason}")
    
    if is_.get('takeaways'):
        print(f"\n  Takeaways:")
        for t in is_['takeaways'][:4]:
            print(f"    • {t[:90]}")
else:
    print("  ✗ invest_smart is None/null!")
