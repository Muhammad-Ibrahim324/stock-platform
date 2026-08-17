"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TooltipContentProps } from "recharts";
import type { RiskResponse } from "@/lib/types";
import { formatDate, formatNumber, formatPercent, formatShortDate } from "@/lib/format";
import { Panel } from "@/components/ui/Panel";

function DrawdownTooltip({ active, payload, label }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-ink-muted">{formatShortDate(label as string)}</p>
      <p className="font-mono tabular-nums text-negative">{formatPercent(payload[0].value as number, { showSign: false })}</p>
    </div>
  );
}

export function RiskPanel({ risk }: { risk: RiskResponse }) {
  return (
    <Panel title="Risk" subtitle={risk.benchmark ? `Benchmarked against ${risk.benchmark}` : "No benchmark selected"}>
      <div className="mb-6 grid grid-cols-2 gap-x-4 gap-y-5 sm:grid-cols-3 lg:grid-cols-4">
        <Metric label="Volatility (ann.)" value={formatPercent(risk.annualized_volatility, { showSign: false })} />
        <Metric label="Sharpe ratio" value={formatNumber(risk.sharpe_ratio)} />
        <Metric label="Sortino ratio" value={formatNumber(risk.sortino_ratio)} />
        <Metric label="Max drawdown" value={formatPercent(risk.max_drawdown_pct, { showSign: false })} tone="negative" />
        <Metric label="Current drawdown" value={formatPercent(risk.current_drawdown_pct, { showSign: false })} />
        <Metric label="VaR (95%, 1d)" value={formatPercent(risk.value_at_risk_95, { showSign: false })} />
        <Metric label="CVaR (95%, 1d)" value={formatPercent(risk.conditional_value_at_risk_95, { showSign: false })} />
        {risk.beta !== null && <Metric label="Beta" value={formatNumber(risk.beta)} />}
        {risk.correlation_to_benchmark !== null && (
          <Metric label="Correlation" value={formatNumber(risk.correlation_to_benchmark)} />
        )}
      </div>

      {risk.max_drawdown_trough_date && (
        <p className="mb-4 text-xs text-ink-faint">
          Worst decline ran from {formatDate(risk.max_drawdown_peak_date!)} to {formatDate(risk.max_drawdown_trough_date)}
          {risk.max_drawdown_recovery_date
            ? `, recovering by ${formatDate(risk.max_drawdown_recovery_date)} (${risk.max_drawdown_recovery_days} days).`
            : " — has not yet recovered to its prior peak within this period."}
        </p>
      )}

      <div className="h-40 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={risk.drawdown_series} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id="drawdownFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#b23434" stopOpacity={0.02} />
                <stop offset="100%" stopColor="#b23434" stopOpacity={0.22} />
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
              tickFormatter={(v: number) => `${v.toFixed(0)}%`}
              width={44}
            />
            <Tooltip content={DrawdownTooltip} />
            <Area
              type="monotone"
              dataKey="drawdown_pct"
              stroke="#b23434"
              strokeWidth={1.25}
              fill="url(#drawdownFill)"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Panel>
  );
}

function Metric({ label, value, tone }: { label: string; value: string; tone?: "negative" }) {
  return (
    <div>
      <p className="text-xs text-ink-faint">{label}</p>
      <p className={`mt-0.5 font-mono text-base font-semibold tabular-nums ${tone === "negative" ? "text-negative" : "text-ink"}`}>
        {value}
      </p>
    </div>
  );
}
