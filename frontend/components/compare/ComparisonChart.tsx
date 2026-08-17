"use client";

import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TooltipContentProps } from "recharts";
import type { CompareSeries } from "@/lib/types";
import { formatPercent, formatShortDate } from "@/lib/format";

const LINE_COLORS = ["#1b3a6b", "#b5762a", "#0b7a56", "#b23434", "#6b4fa0", "#2f7a8c"];

function CompareTooltip({ active, payload, label }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-ink-muted">{formatShortDate(label as string)}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey as string} className="flex items-center gap-2 font-mono tabular-nums">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: entry.color }} />
          <span className="text-ink-faint">{entry.dataKey as string}</span>
          <span className="text-ink">{formatPercent(entry.value as number)}</span>
        </p>
      ))}
    </div>
  );
}

export function ComparisonChart({ series }: { series: CompareSeries[] }) {
  // Merge each ticker's normalized series into one array of {trade_date, TICKER: value, ...}
  const merged = new Map<string, Record<string, number | string>>();
  for (const s of series) {
    for (const point of s.normalized_return_pct) {
      const row = merged.get(point.trade_date) ?? { trade_date: point.trade_date };
      row[s.ticker] = point.value;
      merged.set(point.trade_date, row);
    }
  }
  const data = Array.from(merged.values()).sort((a, b) =>
    (a.trade_date as string).localeCompare(b.trade_date as string)
  );

  return (
    <div className="h-96 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="var(--color-border)" vertical={false} />
          <XAxis
            dataKey="trade_date"
            tickFormatter={formatShortDate}
            tick={{ fontSize: 11, fill: "var(--color-ink-faint)" }}
            tickLine={false}
            axisLine={{ stroke: "var(--color-border)" }}
            minTickGap={56}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "var(--color-ink-faint)" }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(v: number) => `${v.toFixed(0)}%`}
            width={48}
          />
          <ReferenceLine y={0} stroke="var(--color-border-strong)" />
          <Tooltip content={CompareTooltip} />
          <Legend wrapperStyle={{ fontSize: 12, color: "var(--color-ink-muted)" }} />
          {series.map((s, i) => (
            <Line
              key={s.ticker}
              type="monotone"
              dataKey={s.ticker}
              stroke={LINE_COLORS[i % LINE_COLORS.length]}
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
