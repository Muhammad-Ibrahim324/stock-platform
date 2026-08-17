"use client";

import { useEffect, useState, type FormEvent } from "react";
import Link from "next/link";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { TooltipContentProps } from "recharts";
import { useAuth } from "@/contexts/AuthContext";
import { portfolioApi, ApiError } from "@/lib/api";
import type { PortfolioAnalyticsResponse } from "@/lib/types";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";
import { Panel } from "@/components/ui/Panel";
import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { ChartPanelSkeleton, MetricGridSkeleton } from "@/components/dashboard/Skeletons";
import { DataSourceBanner } from "@/components/dashboard/DataSourceBanner";

const ALLOCATION_COLORS = ["#1b3a6b", "#b5762a", "#0b7a56", "#b23434", "#6b4fa0", "#2f7a8c", "#8891a0", "#c9ced6"];

function AllocationTooltip({ active, payload }: TooltipContentProps) {
  if (!active || !payload || payload.length === 0) return null;
  const entry = payload[0];
  return (
    <div className="rounded-md border border-border bg-surface px-3 py-2 text-xs shadow-lg">
      <p className="font-medium text-ink">{entry.name as string}</p>
      <p className="font-mono tabular-nums text-ink-muted">{formatPercent((entry.value as number) * 100, { showSign: false })}</p>
    </div>
  );
}

function AllocationDonut({ allocation }: { allocation: Record<string, number> }) {
  const data = Object.entries(allocation)
    .sort((a, b) => b[1] - a[1])
    .map(([name, value]) => ({ name, value }));
  if (data.length === 0) return <p className="text-sm text-ink-faint">No allocation data yet.</p>;

  return (
    <div className="flex items-center gap-6">
      <div className="h-48 w-48 shrink-0">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={48} outerRadius={80} paddingAngle={2} isAnimationActive={false}>
              {data.map((_, i) => (
                <Cell key={i} fill={ALLOCATION_COLORS[i % ALLOCATION_COLORS.length]} stroke="var(--color-surface)" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip content={AllocationTooltip} />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <ul className="flex flex-1 flex-col gap-1.5 text-sm">
        {data.map((d, i) => (
          <li key={d.name} className="flex items-center justify-between gap-3">
            <span className="flex items-center gap-2 truncate text-ink-muted">
              <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: ALLOCATION_COLORS[i % ALLOCATION_COLORS.length] }} />
              <span className="truncate">{d.name}</span>
            </span>
            <span className="shrink-0 font-mono tabular-nums text-ink">{formatPercent(d.value * 100, { showSign: false })}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function PortfolioView() {
  const { token } = useAuth();
  const [data, setData] = useState<PortfolioAnalyticsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [formTicker, setFormTicker] = useState("");
  const [formShares, setFormShares] = useState("");
  const [formCost, setFormCost] = useState("");
  const [formDate, setFormDate] = useState(new Date().toISOString().slice(0, 10));
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function refresh() {
    if (!token) return;
    try {
      const res = await portfolioApi.analytics(token);
      setData(res);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load your portfolio.");
    }
  }

  useEffect(() => {
    if (!token) return;
    // Inlined (rather than calling refresh()) so every setState here is
    // nested inside a .then/.catch — see WatchlistView for the same pattern.
    portfolioApi
      .analytics(token)
      .then((res) => {
        setData(res);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Couldn't load your portfolio.");
      });
  }, [token]);

  async function handleAddHolding(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    const shares = parseFloat(formShares);
    const cost = parseFloat(formCost);
    if (!formTicker.trim() || !(shares > 0) || !(cost >= 0)) {
      setFormError("Enter a valid ticker, a positive share count, and a non-negative cost basis.");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      await portfolioApi.addHolding(token, {
        ticker: formTicker.trim().toUpperCase(),
        shares,
        cost_basis_per_share: cost,
        purchase_date: formDate,
      });
      setFormTicker("");
      setFormShares("");
      setFormCost("");
      setShowForm(false);
      await refresh();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Couldn't add that holding.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    if (!token) return;
    await portfolioApi.deleteHolding(token, id);
    await refresh();
  }

  if (error) {
    return (
      <div role="alert" className="rounded-lg border border-negative/30 bg-negative-soft px-4 py-3 text-sm text-negative">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col gap-5">
        <MetricGridSkeleton />
        <ChartPanelSkeleton height="h-64" />
      </div>
    );
  }

  const totalPositive = data.total_gain_loss >= 0;

  return (
    <div className="flex flex-col gap-5">
      {data.is_synthetic && <DataSourceBanner />}

      <div className="flex items-center justify-between">
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
          <Stat label="Current value" value={formatCurrency(data.total_current_value)} />
          <Stat label="Cost basis" value={formatCurrency(data.total_cost_basis)} />
          <Stat
            label="Gain / loss"
            value={formatCurrency(data.total_gain_loss)}
            tone={data.holdings.length === 0 ? undefined : totalPositive ? "positive" : "negative"}
          />
          <Stat
            label="Return"
            value={formatPercent(data.total_gain_loss_pct)}
            tone={data.holdings.length === 0 ? undefined : totalPositive ? "positive" : "negative"}
          />
        </div>
        <Button onClick={() => setShowForm((s) => !s)} variant={showForm ? "secondary" : "primary"}>
          {showForm ? "Cancel" : "Add holding"}
        </Button>
      </div>

      {showForm && (
        <Panel>
          <form onSubmit={handleAddHolding} className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Field label="Ticker" value={formTicker} onChange={(e) => setFormTicker(e.target.value.toUpperCase())} placeholder="AAPL" required />
            <Field label="Shares" type="number" step="any" min="0" value={formShares} onChange={(e) => setFormShares(e.target.value)} required />
            <Field label="Cost basis / share" type="number" step="any" min="0" value={formCost} onChange={(e) => setFormCost(e.target.value)} required />
            <Field label="Purchase date" type="date" value={formDate} onChange={(e) => setFormDate(e.target.value)} required />
            {formError && <p className="col-span-full text-sm text-negative">{formError}</p>}
            <Button type="submit" loading={submitting} className="col-span-full sm:col-span-1">
              Add
            </Button>
          </form>
        </Panel>
      )}

      {data.excluded.length > 0 && (
        <div className="rounded-lg border border-accent/30 bg-accent-soft px-4 py-3 text-xs text-ink">
          {data.excluded.map((e) => (
            <p key={e.ticker}>
              <strong className="font-medium">{e.ticker}</strong>: {e.reason}
            </p>
          ))}
        </div>
      )}

      {data.holdings.length === 0 ? (
        <p className="text-sm text-ink-faint">No holdings yet — add one above to see your portfolio analytics.</p>
      ) : (
        <>
          <Panel title="Holdings">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-ink-faint">
                  <th className="py-2 pr-4 font-medium">Ticker</th>
                  <th className="py-2 pl-4 text-right font-medium">Shares</th>
                  <th className="py-2 pl-4 text-right font-medium">Cost / share</th>
                  <th className="py-2 pl-4 text-right font-medium">Value</th>
                  <th className="py-2 pl-4 text-right font-medium">Gain / loss</th>
                  <th className="py-2 pl-4 text-right font-medium">Weight</th>
                  <th className="py-2 pl-4" />
                </tr>
              </thead>
              <tbody>
                {data.holdings.map((h) => {
                  const positive = (h.gain_loss ?? 0) >= 0;
                  return (
                    <tr key={h.id} className="border-b border-border/60">
                      <td className="py-3 pr-4">
                        <Link href={`/research/${h.ticker}`} className="font-mono font-medium text-ink hover:text-primary">
                          {h.ticker}
                        </Link>
                      </td>
                      <td className="py-3 pl-4 text-right font-mono tabular-nums text-ink-muted">{formatNumber(h.shares, 2)}</td>
                      <td className="py-3 pl-4 text-right font-mono tabular-nums text-ink-muted">{formatCurrency(h.cost_basis_per_share)}</td>
                      <td className="py-3 pl-4 text-right font-mono tabular-nums text-ink">{formatCurrency(h.current_value)}</td>
                      <td className={`py-3 pl-4 text-right font-mono tabular-nums ${h.gain_loss === null ? "text-ink-faint" : positive ? "text-positive" : "text-negative"}`}>
                        {h.gain_loss === null ? "N/A" : `${formatCurrency(h.gain_loss)} (${formatPercent(h.gain_loss_pct ?? 0)})`}
                      </td>
                      <td className="py-3 pl-4 text-right font-mono tabular-nums text-ink-muted">
                        {h.weight_pct === null ? "N/A" : `${h.weight_pct.toFixed(1)}%`}
                      </td>
                      <td className="py-3 pl-4 text-right">
                        <button type="button" onClick={() => handleDelete(h.id)} className="text-xs text-ink-faint transition-colors duration-[var(--duration-fast)] hover:text-negative">
                          Remove
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            <Panel title="Allocation" subtitle="By ticker">
              <AllocationDonut allocation={data.allocation_by_ticker} />
            </Panel>
            {Object.keys(data.allocation_by_sector).length > 0 && (
              <Panel title="Allocation" subtitle="By sector">
                <AllocationDonut allocation={data.allocation_by_sector} />
              </Panel>
            )}
          </div>

          <Panel title="Risk" subtitle="Based on the current mix of holdings">
            <p className="mb-4 text-xs text-ink-faint">{data.risk_note}</p>
            {data.risk ? (
              <div className="grid grid-cols-2 gap-x-4 gap-y-5 sm:grid-cols-3">
                <Stat label="Volatility (ann.)" value={formatPercent(data.risk.annualized_volatility, { showSign: false })} small />
                <Stat label="Sharpe ratio" value={formatNumber(data.risk.sharpe_ratio)} small />
                <Stat label="Sortino ratio" value={formatNumber(data.risk.sortino_ratio)} small />
                <Stat label="Max drawdown" value={formatPercent(data.risk.max_drawdown_pct, { showSign: false })} small tone="negative" />
                {data.risk.beta !== null && <Stat label="Beta (vs SPY)" value={formatNumber(data.risk.beta)} small />}
                {data.risk.correlation_to_benchmark !== null && (
                  <Stat label="Correlation (vs SPY)" value={formatNumber(data.risk.correlation_to_benchmark)} small />
                )}
              </div>
            ) : (
              <p className="text-sm text-ink-faint">Not enough data to compute risk metrics yet.</p>
            )}
          </Panel>
        </>
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  tone,
  small,
}: {
  label: string;
  value: string;
  tone?: "positive" | "negative";
  small?: boolean;
}) {
  return (
    <div>
      <p className="text-xs text-ink-faint">{label}</p>
      <p
        className={`mt-0.5 font-mono font-semibold tabular-nums ${small ? "text-base" : "text-xl"} ${
          tone === "positive" ? "text-positive" : tone === "negative" ? "text-negative" : "text-ink"
        }`}
      >
        {value}
      </p>
    </div>
  );
}
