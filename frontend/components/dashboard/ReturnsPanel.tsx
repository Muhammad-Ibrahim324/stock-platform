"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TooltipContentProps } from "recharts";
import clsx from "clsx";
import type { ReturnsResponse } from "@/lib/types";
import { formatCurrency, formatPercent, formatShortDate } from "@/lib/format";
import { Panel } from "@/components/ui/Panel";

function GrowthTooltip({ active, payload, label }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-ink-muted">{formatShortDate(label as string)}</p>
      <p className="font-mono tabular-nums text-ink">{formatCurrency(payload[0].value as number)}</p>
    </div>
  );
}

export function ReturnsPanel({ returns }: { returns: ReturnsResponse }) {
  const positive = returns.total_return_pct >= 0;
  const lineColor = positive ? "#0b7a56" : "#b23434";

  return (
    <Panel title="Returns" subtitle={`Growth of ${formatCurrency(returns.initial_investment, { decimals: 0 })} invested at the start of the period`}>
      <div className="mb-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Total return" value={formatPercent(returns.total_return_pct)} positive={positive} />
        <Stat label="Annualized" value={formatPercent(returns.annualized_return_pct)} positive={returns.annualized_return_pct >= 0} />
        <Stat label="Ending value" value={formatCurrency(returns.ending_value)} mono />
        <Stat label="Daily σ (std dev)" value={`${returns.distribution.std_pct.toFixed(2)}%`} mono />
      </div>

      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={returns.growth_series} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="growthFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={lineColor} stopOpacity={0.16} />
                <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="trade_date"
              tickFormatter={formatShortDate}
              tick={{ fontSize: 11, fill: "var(--color-ink-faint)" }}
              tickLine={false}
              axisLine={{ stroke: "var(--color-border)" }}
              minTickGap={48}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--color-ink-faint)" }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => formatCurrency(v, { decimals: 0 })}
              width={64}
            />
            <Tooltip content={GrowthTooltip} />
            <Area type="monotone" dataKey="value" stroke={lineColor} strokeWidth={1.75} fill="url(#growthFill)" isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  );
}

function Stat({ label, value, positive, mono }: { label: string; value: string; positive?: boolean; mono?: boolean }) {
  return (
    <div>
      <p className="text-xs text-ink-faint">{label}</p>
      <p
        className={clsx(
          "mt-0.5 font-mono text-lg font-semibold tabular-nums",
          positive === undefined ? "text-ink" : positive ? "text-positive" : "text-negative",
          mono && "font-mono"
        )}
      >
        {value}
      </p>
    </div>
  );
}
