"use client";

import { Bar, Cell, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TooltipContentProps } from "recharts";
import type { IndicatorPoint } from "@/lib/types";
import { formatShortDate } from "@/lib/format";
import { Panel } from "@/components/ui/Panel";

function RsiTooltip({ active, payload, label }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null;
  const value = payload[0].value as number | null;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-ink-muted">{formatShortDate(label as string)}</p>
      <p className="font-mono tabular-nums text-ink">RSI {value !== null ? value.toFixed(1) : "N/A"}</p>
    </div>
  );
}

function MacdTooltip({ active, payload, label }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-ink-muted">{formatShortDate(label as string)}</p>
      {payload.map((p) => (
        <p key={p.dataKey as string} className="font-mono tabular-nums text-ink">
          {p.name}: {typeof p.value === "number" ? p.value.toFixed(2) : "N/A"}
        </p>
      ))}
    </div>
  );
}

export function TechnicalsPanel({ points }: { points: IndicatorPoint[] }) {
  return (
    <Panel title="Technical indicators" subtitle="RSI (14) and MACD (12, 26, 9)">
      <div className="space-y-6">
        <div>
          <p className="mb-2 text-xs font-medium text-ink-muted">RSI (14)</p>
          <div className="h-32 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={points} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                <XAxis
                  dataKey="trade_date"
                  tickFormatter={formatShortDate}
                  tick={{ fontSize: 10, fill: "var(--color-ink-faint)" }}
                  tickLine={false}
                  axisLine={{ stroke: "var(--color-border)" }}
                  minTickGap={64}
                />
                <YAxis domain={[0, 100]} ticks={[30, 50, 70]} tick={{ fontSize: 10, fill: "var(--color-ink-faint)" }} tickLine={false} axisLine={false} width={28} />
                <ReferenceLine y={70} stroke="var(--color-negative)" strokeDasharray="3 3" strokeOpacity={0.5} />
                <ReferenceLine y={30} stroke="var(--color-positive)" strokeDasharray="3 3" strokeOpacity={0.5} />
                <Tooltip content={RsiTooltip} />
                <Line type="monotone" dataKey="rsi_14" stroke="#1b3a6b" strokeWidth={1.25} dot={false} isAnimationActive={false} connectNulls />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-1 text-[11px] text-ink-faint">Above 70 is conventionally read as overbought, below 30 as oversold.</p>
        </div>

        <div>
          <p className="mb-2 text-xs font-medium text-ink-muted">MACD</p>
          <div className="h-32 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={points} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                <XAxis
                  dataKey="trade_date"
                  tickFormatter={formatShortDate}
                  tick={{ fontSize: 10, fill: "var(--color-ink-faint)" }}
                  tickLine={false}
                  axisLine={{ stroke: "var(--color-border)" }}
                  minTickGap={64}
                />
                <YAxis tick={{ fontSize: 10, fill: "var(--color-ink-faint)" }} tickLine={false} axisLine={false} width={36} />
                <ReferenceLine y={0} stroke="var(--color-border-strong)" />
                <Tooltip content={MacdTooltip} />
                <Bar dataKey="macd_histogram" name="Histogram" isAnimationActive={false}>
                  {points.map((p, i) => (
                    <Cell key={i} fill={(p.macd_histogram ?? 0) >= 0 ? "var(--color-positive)" : "var(--color-negative)"} fillOpacity={0.35} />
                  ))}
                </Bar>
                <Line type="monotone" dataKey="macd" name="MACD" stroke="#1b3a6b" strokeWidth={1.25} dot={false} isAnimationActive={false} connectNulls />
                <Line type="monotone" dataKey="macd_signal" name="Signal" stroke="#b5762a" strokeWidth={1.25} dot={false} isAnimationActive={false} connectNulls />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </Panel>
  );
}
