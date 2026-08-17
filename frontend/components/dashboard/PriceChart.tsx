"use client";

import { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { TooltipContentProps } from "recharts";
import clsx from "clsx";
import { formatCurrency, formatShortDate } from "@/lib/format";

export interface PriceChartPoint {
  trade_date: string;
  close: number;
  sma_20: number | null;
  sma_50: number | null;
}

const OVERLAYS = [
  { key: "sma_20" as const, label: "SMA 20", color: "#b5762a" },
  { key: "sma_50" as const, label: "SMA 50", color: "#1b3a6b" },
];

function ChartTooltip({ active, payload, label }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-ink-muted">{formatShortDate(label as string)}</p>
      {payload.map((entry) => (
        <p key={entry.dataKey as string} className="flex items-center gap-2 font-mono tabular-nums">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: entry.color }} />
          <span className="text-ink-faint">{entry.name}</span>
          <span className="text-ink">{formatCurrency(entry.value as number)}</span>
        </p>
      ))}
    </div>
  );
}

export function PriceChart({ data, isPositivePeriod }: { data: PriceChartPoint[]; isPositivePeriod: boolean }) {
  const [activeOverlays, setActiveOverlays] = useState<Set<string>>(new Set());
  const lineColor = isPositivePeriod ? "#0b7a56" : "#b23434";

  const domain = useMemo(() => {
    const closes = data.map((d) => d.close).filter((v) => Number.isFinite(v));
    if (closes.length === 0) return undefined;
    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const pad = (max - min) * 0.08 || max * 0.02;
    return [min - pad, max + pad] as [number, number];
  }, [data]);

  function toggleOverlay(key: string) {
    setActiveOverlays((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        {OVERLAYS.map((o) => (
          <button
            key={o.key}
            type="button"
            onClick={() => toggleOverlay(o.key)}
            className={clsx(
              "flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-medium transition-colors duration-[var(--duration-fast)]",
              activeOverlays.has(o.key)
                ? "border-transparent bg-surface-sunken text-ink"
                : "border-border text-ink-faint hover:text-ink-muted"
            )}
          >
            <span className="inline-block h-2 w-2 rounded-full" style={{ background: o.color }} />
            {o.label}
          </button>
        ))}
      </div>

      <div className="h-72 w-full sm:h-96">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={lineColor} stopOpacity={0.18} />
                <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--color-border)" strokeDasharray="0" vertical={false} />
            <XAxis
              dataKey="trade_date"
              tickFormatter={formatShortDate}
              tick={{ fontSize: 11, fill: "var(--color-ink-faint)" }}
              tickLine={false}
              axisLine={{ stroke: "var(--color-border)" }}
              minTickGap={48}
            />
            <YAxis
              domain={domain}
              tick={{ fontSize: 11, fill: "var(--color-ink-faint)" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => formatCurrency(v, { decimals: 0 })}
              width={56}
            />
            <Tooltip content={ChartTooltip} />
            <Area
              type="monotone"
              dataKey="close"
              name="Price"
              stroke={lineColor}
              strokeWidth={1.75}
              fill="url(#priceFill)"
              isAnimationActive={true}
              animationDuration={450}
              animationEasing="ease-out"
            />
            {OVERLAYS.filter((o) => activeOverlays.has(o.key)).map((o) => (
              <Line
                key={o.key}
                type="monotone"
                dataKey={o.key}
                name={o.label}
                stroke={o.color}
                strokeWidth={1.25}
                dot={false}
                isAnimationActive={true}
                animationDuration={450}
                animationEasing="ease-out"
                connectNulls
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
