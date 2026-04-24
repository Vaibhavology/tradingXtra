"use client";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

interface DataPoint {
  timestamp: string | null;
  capital: number;
  trade_num: number;
}

export default function EquityChart({ data, initial }: { data: DataPoint[]; initial: number }) {
  const chartData = data.map((d, i) => ({
    idx: i,
    label: d.trade_num ? `T${d.trade_num}` : "Start",
    capital: d.capital,
  }));

  const min = Math.min(...chartData.map(d => d.capital)) * 0.995;
  const max = Math.max(...chartData.map(d => d.capital)) * 1.005;

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={chartData} margin={{ top: 5, right: 5, left: 10, bottom: 5 }}>
        <defs>
          <linearGradient id="eqGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="label"
          tick={{ fill: "#6b7280", fontSize: 10 }}
          tickLine={false}
          axisLine={{ stroke: "#2a3040" }}
        />
        <YAxis
          domain={[min, max]}
          tick={{ fill: "#6b7280", fontSize: 10 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v: any) => `₹${(v / 1000).toFixed(0)}k`}
        />
        <Tooltip
          contentStyle={{
            background: "#1a1f2e",
            border: "1px solid #2a3040",
            borderRadius: "8px",
            fontSize: "12px",
            color: "#e5e7eb",
          }}
          formatter={(v: any) => [`₹${Number(v).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`, "Capital"]}
        />
        <ReferenceLine y={initial} stroke="#4b5563" strokeDasharray="3 3" />
        <Area
          type="monotone"
          dataKey="capital"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="url(#eqGrad)"
          dot={false}
          activeDot={{ r: 4, fill: "#3b82f6", stroke: "#1a1f2e", strokeWidth: 2 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
