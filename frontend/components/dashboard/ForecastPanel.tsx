"use client";

import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TooltipContentProps } from "recharts";
import clsx from "clsx";
import { api, ApiError } from "@/lib/api";
import type { ForecastResponse } from "@/lib/types";
import { formatNumber, formatPercent, formatShortDate } from "@/lib/format";
import { Panel } from "@/components/ui/Panel";
import { ChartPanelSkeleton } from "./Skeletons";

function ForecastTooltip({ active, payload, label }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-ink-muted">{formatShortDate(label as string)}</p>
      {payload.map((p) => (
        <p key={p.dataKey as string} className="font-mono tabular-nums text-ink">
          {p.name}: {typeof p.value === "number" ? formatPercent(p.value) : "N/A"}
        </p>
      ))}
    </div>
  );
}

function VerdictBadge({ label, won }: { label: string; won: boolean | null }) {
  if (won === null) return null;
  return (
    <span
      className={clsx(
        "rounded-md px-2 py-0.5 text-xs font-medium",
        won ? "bg-positive-soft text-positive" : "bg-negative-soft text-negative"
      )}
    >
      {label}: {won ? "beats baseline" : "does not beat baseline"}
    </span>
  );
}

export function ForecastPanel({ ticker }: { ticker: string }) {
  const [data, setData] = useState<ForecastResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [settledTicker, setSettledTicker] = useState<string | null>(null);
  const loading = settledTicker !== ticker;

  useEffect(() => {
    let cancelled = false;
    api
      .getForecast(ticker, "2y")
      .then((res) => {
        if (cancelled) return;
        setData(res);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "Couldn't load the forecast right now.");
      })
      .finally(() => {
        if (!cancelled) setSettledTicker(ticker);
      });
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  if (loading) return <ChartPanelSkeleton height="h-64" />;
  if (error) {
    return (
      <Panel title="Forecast">
        <p role="alert" className="text-sm text-negative">
          {error}
        </p>
      </Panel>
    );
  }
  if (!data) return null;

  const nextUp = (data.next_predicted_return_pct ?? 0) >= 0;

  return (
    <Panel title="Forecast" subtitle="Walk-forward evaluated ridge regression, checked against a naive baseline">
      <div className="mb-4 rounded-md border border-accent/30 bg-accent-soft px-3 py-2 text-xs leading-relaxed text-ink">
        {data.disclaimer}
      </div>

      <div className="mb-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div>
          <p className="text-xs text-ink-faint">Next-day prediction</p>
          <p className={clsx("mt-0.5 font-mono text-lg font-semibold tabular-nums", nextUp ? "text-positive" : "text-negative")}>
            {formatPercent(data.next_predicted_return_pct)}
          </p>
        </div>
        <div>
          <p className="text-xs text-ink-faint">Directional accuracy</p>
          <p className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-ink">
            {data.model_directional_accuracy_pct?.toFixed(1)}%
          </p>
        </div>
        <div>
          <p className="text-xs text-ink-faint">Model MAE</p>
          <p className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-ink">{formatNumber(data.model_mae_pct, 3)}%</p>
        </div>
        <div>
          <p className="text-xs text-ink-faint">Out-of-sample days</p>
          <p className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-ink">{data.n_predictions}</p>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        <VerdictBadge label="MAE vs. zero baseline" won={data.beats_naive_mae} />
        <VerdictBadge label="Direction vs. 50/50" won={data.beats_naive_directional} />
      </div>

      <div className="h-56 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data.chart_series} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="actualFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#1b3a6b" stopOpacity={0.12} />
                <stop offset="100%" stopColor="#1b3a6b" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis
              dataKey="trade_date"
              tickFormatter={formatShortDate}
              tick={{ fontSize: 10, fill: "var(--color-ink-faint)" }}
              tickLine={false}
              axisLine={{ stroke: "var(--color-border)" }}
              minTickGap={64}
            />
            <YAxis tick={{ fontSize: 10, fill: "var(--color-ink-faint)" }} tickLine={false} axisLine={false} tickFormatter={(v: number) => `${v.toFixed(1)}%`} width={44} />
            <ReferenceLine y={0} stroke="var(--color-border-strong)" />
            <Tooltip content={ForecastTooltip} />
            <Area type="monotone" dataKey="actual_pct" name="Actual" stroke="#1b3a6b" strokeWidth={1} fill="url(#actualFill)" isAnimationActive={false} dot={false} />
            <Line type="monotone" dataKey="predicted_pct" name="Predicted" stroke="#b5762a" strokeWidth={1.25} dot={false} isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-2 text-[11px] text-ink-faint">
        Actual vs. predicted next-day return, out-of-sample only — every point here was predicted before that
        day&apos;s data existed.
      </p>
    </Panel>
  );
}
