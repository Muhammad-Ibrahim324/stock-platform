"use client";

import { useEffect, useState, type FormEvent } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { TooltipContentProps } from "recharts";
import clsx from "clsx";
import { api, ApiError } from "@/lib/api";
import type { BacktestResponse, BacktestStrategy } from "@/lib/types";
import { formatNumber, formatPercent, formatShortDate } from "@/lib/format";
import { Panel } from "@/components/ui/Panel";
import { Button } from "@/components/ui/Button";
import { ChartPanelSkeleton } from "./Skeletons";

const STRATEGIES: { value: BacktestStrategy; label: string }[] = [
  { value: "sma_crossover", label: "SMA crossover" },
  { value: "rsi_mean_reversion", label: "RSI mean reversion" },
  { value: "buy_and_hold", label: "Buy & hold" },
];

function EquityTooltip({ active, payload, label }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-ink-muted">{formatShortDate(label as string)}</p>
      {payload.map((p) => (
        <p key={p.dataKey as string} className="font-mono tabular-nums text-ink">
          {p.name}: {typeof p.value === "number" ? p.value.toFixed(3) : "N/A"}
        </p>
      ))}
    </div>
  );
}

function MetricsTable({ strategy, buyHold }: { strategy: BacktestResponse["strategy_metrics"]; buyHold: BacktestResponse["buy_hold_metrics"] }) {
  const rows: { label: string; s: number; b: number; suffix: string; higherIsBetter: boolean }[] = [
    { label: "Total return", s: strategy.total_return_pct, b: buyHold.total_return_pct, suffix: "%", higherIsBetter: true },
    { label: "Annualized return", s: strategy.annualized_return_pct, b: buyHold.annualized_return_pct, suffix: "%", higherIsBetter: true },
    { label: "Volatility (ann.)", s: strategy.annualized_volatility_pct, b: buyHold.annualized_volatility_pct, suffix: "%", higherIsBetter: false },
    { label: "Sharpe", s: strategy.sharpe_ratio, b: buyHold.sharpe_ratio, suffix: "", higherIsBetter: true },
    { label: "Sortino", s: strategy.sortino_ratio, b: buyHold.sortino_ratio, suffix: "", higherIsBetter: true },
    { label: "Max drawdown", s: strategy.max_drawdown_pct, b: buyHold.max_drawdown_pct, suffix: "%", higherIsBetter: true },
  ];
  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="border-b border-border text-left text-xs text-ink-faint">
          <th className="py-2 pr-4 font-medium">Metric</th>
          <th className="py-2 pl-4 text-right font-medium">Strategy</th>
          <th className="py-2 pl-4 text-right font-medium">Buy &amp; hold</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.label} className="border-b border-border/60">
            <td className="py-2 pr-4 text-ink-muted">{r.label}</td>
            <td
              className={clsx(
                "py-2 pl-4 text-right font-mono tabular-nums",
                r.higherIsBetter ? (r.s >= r.b ? "text-positive" : "text-ink") : r.s <= r.b ? "text-positive" : "text-ink"
              )}
            >
              {r.s.toFixed(2)}
              {r.suffix}
            </td>
            <td className="py-2 pl-4 text-right font-mono tabular-nums text-ink-muted">
              {r.b.toFixed(2)}
              {r.suffix}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export function BacktestPanel({ ticker }: { ticker: string }) {
  const [strategy, setStrategy] = useState<BacktestStrategy>("sma_crossover");
  const [fast, setFast] = useState("20");
  const [slow, setSlow] = useState("50");
  const [oversold, setOversold] = useState("30");
  const [overbought, setOverbought] = useState("70");
  const [costBps, setCostBps] = useState("10");
  const [slippageBps, setSlippageBps] = useState("5");

  const [data, setData] = useState<BacktestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [settledTicker, setSettledTicker] = useState<string | null>(null);
  const [manualLoading, setManualLoading] = useState(false);
  const loading = manualLoading || settledTicker !== ticker;

  async function run(e?: FormEvent) {
    e?.preventDefault();
    setManualLoading(true);
    setError(null);
    try {
      const res = await api.getBacktest(ticker, {
        strategy,
        period: "2y",
        fast: Number(fast),
        slow: Number(slow),
        oversold: Number(oversold),
        overbought: Number(overbought),
        transaction_cost_bps: Number(costBps),
        slippage_bps: Number(slippageBps),
      });
      setData(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't run this backtest right now.");
    } finally {
      setManualLoading(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    api
      .getBacktest(ticker, {
        strategy: "sma_crossover",
        period: "2y",
        fast: 20,
        slow: 50,
        transaction_cost_bps: 10,
        slippage_bps: 5,
      })
      .then((res) => {
        if (cancelled) return;
        setData(res);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "Couldn't run this backtest right now.");
      })
      .finally(() => {
        if (!cancelled) setSettledTicker(ticker);
      });
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  return (
    <Panel title="Backtest" subtitle="Simple rules-based strategies against historical prices, including costs">
      <form onSubmit={run} className="mb-4 flex flex-wrap items-end gap-3">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-ink-muted" htmlFor="strategy">
            Strategy
          </label>
          <select
            id="strategy"
            value={strategy}
            onChange={(e) => setStrategy(e.target.value as BacktestStrategy)}
            className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:border-primary focus:outline-none"
          >
            {STRATEGIES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {strategy === "sma_crossover" && (
          <>
            <MiniField label="Fast SMA" value={fast} onChange={setFast} />
            <MiniField label="Slow SMA" value={slow} onChange={setSlow} />
          </>
        )}
        {strategy === "rsi_mean_reversion" && (
          <>
            <MiniField label="Oversold" value={oversold} onChange={setOversold} />
            <MiniField label="Overbought" value={overbought} onChange={setOverbought} />
          </>
        )}
        <MiniField label="Cost (bps)" value={costBps} onChange={setCostBps} />
        <MiniField label="Slippage (bps)" value={slippageBps} onChange={setSlippageBps} />

        <Button type="submit" loading={loading} size="sm">
          Run backtest
        </Button>
      </form>

      {error && (
        <p role="alert" className="mb-4 text-sm text-negative">
          {error}
        </p>
      )}

      {loading && !data && <ChartPanelSkeleton height="h-56" />}

      {data && (
        <>
          <div className="mb-4 rounded-md border border-accent/30 bg-accent-soft px-3 py-2 text-xs leading-relaxed text-ink">
            {data.disclaimer}
          </div>

          <div className="mb-5 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-xs text-ink-faint">Outperformance vs. buy &amp; hold</p>
              <p
                className={clsx(
                  "mt-0.5 font-mono text-lg font-semibold tabular-nums",
                  data.outperformance_pct >= 0 ? "text-positive" : "text-negative"
                )}
              >
                {formatPercent(data.outperformance_pct)}
              </p>
            </div>
            <div>
              <p className="text-xs text-ink-faint">Trades</p>
              <p className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-ink">{data.num_trades}</p>
            </div>
            <div>
              <p className="text-xs text-ink-faint">Total cost drag</p>
              <p className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-ink">{formatNumber(data.total_costs_pct, 2)}%</p>
            </div>
            <div>
              <p className="text-xs text-ink-faint">Sharpe (strategy)</p>
              <p className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-ink">{data.strategy_metrics.sharpe_ratio.toFixed(2)}</p>
            </div>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.equity_curve} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                <CartesianGrid stroke="var(--color-border)" vertical={false} />
                <XAxis
                  dataKey="trade_date"
                  tickFormatter={formatShortDate}
                  tick={{ fontSize: 10, fill: "var(--color-ink-faint)" }}
                  tickLine={false}
                  axisLine={{ stroke: "var(--color-border)" }}
                  minTickGap={64}
                />
                <YAxis tick={{ fontSize: 10, fill: "var(--color-ink-faint)" }} tickLine={false} axisLine={false} width={40} />
                <Tooltip content={EquityTooltip} />
                <Legend wrapperStyle={{ fontSize: 12, color: "var(--color-ink-muted)" }} />
                <Line type="monotone" dataKey="strategy_value" name="Strategy" stroke="#1b3a6b" strokeWidth={1.5} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="buy_hold_value" name="Buy & hold" stroke="#8891a0" strokeWidth={1.25} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-5">
            <MetricsTable strategy={data.strategy_metrics} buyHold={data.buy_hold_metrics} />
          </div>
        </>
      )}
    </Panel>
  );
}

function MiniField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-ink-muted">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-20 rounded-md border border-border bg-surface px-2 py-2 text-sm text-ink focus:border-primary focus:outline-none"
      />
    </div>
  );
}
