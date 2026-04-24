import { useEffect, useState } from "react";

export default function OrderBookCard({ symbol = "NIFTY" }: { symbol?: string }) {
  const [bids, setBids] = useState<{ price: number; size: number; total: number }[]>([]);
  const [asks, setAsks] = useState<{ price: number; size: number; total: number }[]>([]);
  const [spread, setSpread] = useState(0);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Determine the correct WebSocket URL based on the current window location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = process.env.NEXT_PUBLIC_API_URL 
      ? process.env.NEXT_PUBLIC_API_URL.replace('http', 'ws').replace('/api', '') + `/api/ws/orderbook?symbol=${symbol}`
      : `${protocol}//localhost:8000/api/ws/orderbook?symbol=${symbol}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "orderbook" && payload.data) {
          // Parse asks
          let totalAsk = 0;
          const parsedAsks = payload.data.asks.map((a: any) => {
            totalAsk += a.volume;
            return { price: a.price, size: a.volume, total: totalAsk };
          }).reverse(); // Reverse asks so highest price is at top

          // Parse bids
          let totalBid = 0;
          const parsedBids = payload.data.bids.map((b: any) => {
            totalBid += b.volume;
            return { price: b.price, size: b.volume, total: totalBid };
          });

          setAsks(parsedAsks);
          setBids(parsedBids);
          
          if (parsedAsks.length > 0 && parsedBids.length > 0) {
            setSpread(parsedAsks[parsedAsks.length - 1].price - parsedBids[0].price);
          }
        }
      } catch (err) {
        console.error("Failed to parse orderbook ws message", err);
      }
    };

    return () => {
      ws.close();
    };
  }, [symbol]);

  const maxTotal = Math.max(
    asks.length > 0 ? asks[0].total : 0, 
    bids.length > 0 ? bids[bids.length - 1].total : 0
  );

  return (
    <div className="bg-[var(--bg-card)] border border-[var(--border-default)] rounded-lg p-4 flex flex-col h-full">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Order Book</h2>
        <span className="text-xs font-mono bg-[var(--bg-secondary)] px-2 py-0.5 rounded text-[var(--text-muted)] border border-[var(--border-default)]">
          {symbol}
        </span>
      </div>

      <div className="flex text-[10px] uppercase text-[var(--text-muted)] font-semibold mb-2 px-1">
        <div className="w-1/3 text-left">Price</div>
        <div className="w-1/3 text-right">Size</div>
        <div className="w-1/3 text-right">Sum</div>
      </div>

      <div className="flex-1 flex flex-col font-mono text-[11px]">
        {/* Asks (Sell Orders - Red) */}
        <div className="flex flex-col-reverse gap-0.5 mb-2">
          {asks.map((ask, i) => (
            <div key={`ask-${i}`} className="flex items-center relative py-1 px-1 group hover:bg-[var(--bg-secondary)] rounded-sm">
              <div 
                className="absolute right-0 top-0 bottom-0 bg-[var(--accent-red)]/10 z-0" 
                style={{ width: `${(ask.total / maxTotal) * 100}%` }}
              />
              <div className="w-1/3 text-left text-[var(--accent-red)] z-10">{ask.price.toFixed(2)}</div>
              <div className="w-1/3 text-right text-white z-10">{ask.size}</div>
              <div className="w-1/3 text-right text-[var(--text-muted)] z-10">{ask.total}</div>
            </div>
          ))}
        </div>

        {/* Spread Indicator */}
        <div className="py-2 flex items-center justify-between border-y border-[var(--border-default)]/50 my-1 bg-[var(--bg-secondary)]/30 px-2 rounded-sm">
          <span className="text-[10px] text-[var(--text-muted)] uppercase">Spread</span>
          <span className="font-bold text-white">{spread.toFixed(2)}</span>
        </div>

        {/* Bids (Buy Orders - Green) */}
        <div className="flex flex-col gap-0.5 mt-2">
          {bids.map((bid, i) => (
            <div key={`bid-${i}`} className="flex items-center relative py-1 px-1 group hover:bg-[var(--bg-secondary)] rounded-sm">
              <div 
                className="absolute right-0 top-0 bottom-0 bg-[var(--accent-green)]/10 z-0" 
                style={{ width: `${(bid.total / maxTotal) * 100}%` }}
              />
              <div className="w-1/3 text-left text-[var(--accent-green)] z-10">{bid.price.toFixed(2)}</div>
              <div className="w-1/3 text-right text-white z-10">{bid.size}</div>
              <div className="w-1/3 text-right text-[var(--text-muted)] z-10">{bid.total}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
