"use client";

import { useState, type FormEvent } from "react";
import Link from "next/link";
import { screenerApi, ApiError } from "@/lib/api";
import type { ScreenerCriteria, ScreenerResponse } from "@/lib/types";
import { formatCurrency, formatLargeCurrency, formatPercent } from "@/lib/format";
import { Panel } from "@/components/ui/Panel";
import { Button } from "@/components/ui/Button";
import { ChartPanelSkeleton } from "@/components/dashboard/Skeletons";
import { DataSourceBanner } from "@/components/dashboard/DataSourceBanner";

const SECTORS = [
  "Communication Services",
  "Consumer Discretionary",
  "Consumer Staples",
  "Energy",
  "Financials",
  "Healthcare",
  "Industrials",
  "Materials",
  "Real Estate",
  "Technology",
  "Utilities",
];

export function ScreenerView() {
  const [sector, setSector] = useState("");
  const [minMarketCap, setMinMarketCap] = useState("");
  const [maxPe, setMaxPe] = useState("");
  const [minDividendYield, setMinDividendYield] = useState("");
  const [candidateLimit, setCandidateLimit] = useState("60");
  const [result, setResult] = useState<ScreenerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  async function runScreen(e?: FormEvent) {
    e?.preventDefault();
    setLoading(true);
    setError(null);
    setHasSearched(true);
    const criteria: ScreenerCriteria = {
      sector: sector || undefined,
      min_market_cap: minMarketCap ? Number(minMarketCap) * 1_000_000_000 : undefined,
      max_pe: maxPe ? Number(maxPe) : undefined,
      min_dividend_yield: minDividendYield ? Number(minDividendYield) : undefined,
      candidate_limit: Number(candidateLimit),
    };
    try {
      const res = await screenerApi.screen(criteria);
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't run the screen right now.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-5">
      <Panel title="Filters">
        <form onSubmit={runScreen} className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-ink-muted" htmlFor="sector">
              Sector
            </label>
            <select
              id="sector"
              value={sector}
              onChange={(e) => setSector(e.target.value)}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:border-primary focus:outline-none"
            >
              <option value="">All sectors</option>
              {SECTORS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <NumberField label="Min market cap ($B)" value={minMarketCap} onChange={setMinMarketCap} />
          <NumberField label="Max P/E" value={maxPe} onChange={setMaxPe} />
          <NumberField label="Min dividend yield (%)" value={minDividendYield} onChange={setMinDividendYield} />
          <div>
            <label className="mb-1.5 block text-xs font-medium text-ink-muted" htmlFor="candidate-limit">
              Candidates to scan
            </label>
            <select
              id="candidate-limit"
              value={candidateLimit}
              onChange={(e) => setCandidateLimit(e.target.value)}
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink focus:border-primary focus:outline-none"
            >
              <option value="30">30 (fastest)</option>
              <option value="60">60</option>
              <option value="100">100</option>
              <option value="150">150 (slowest)</option>
            </select>
          </div>
          <Button type="submit" loading={loading} className="col-span-2 sm:col-span-1 sm:self-end">
            Run screen
          </Button>
        </form>
      </Panel>

      {error && (
        <div role="alert" className="rounded-lg border border-negative/30 bg-negative-soft px-4 py-3 text-sm text-negative">
          {error}
        </div>
      )}

      {loading && <ChartPanelSkeleton height="h-64" />}

      {!loading && result && (
        <>
          {result.is_synthetic && <DataSourceBanner />}
          <p className="text-xs text-ink-faint">{result.note}</p>

          {result.results.length === 0 ? (
            <p className="text-sm text-ink-faint">No candidates matched these filters.</p>
          ) : (
            <Panel>
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr className="border-b border-border text-left text-xs text-ink-faint">
                    <th className="py-2 pr-4 font-medium">Ticker</th>
                    <th className="py-2 pr-4 font-medium">Company</th>
                    <th className="py-2 pr-4 font-medium">Sector</th>
                    <th className="py-2 pl-4 text-right font-medium">Price</th>
                    <th className="py-2 pl-4 text-right font-medium">Change</th>
                    <th className="py-2 pl-4 text-right font-medium">Mkt cap</th>
                    <th className="py-2 pl-4 text-right font-medium">P/E</th>
                  </tr>
                </thead>
                <tbody>
                  {result.results.map((r) => {
                    const positive = (r.change_percent ?? 0) >= 0;
                    return (
                      <tr key={r.ticker} className="border-b border-border/60">
                        <td className="py-3 pr-4">
                          <Link href={`/research/${r.ticker}`} className="font-mono font-medium text-ink hover:text-primary">
                            {r.ticker}
                          </Link>
                        </td>
                        <td className="max-w-[200px] truncate py-3 pr-4 text-ink-muted">{r.company_name}</td>
                        <td className="py-3 pr-4 text-ink-faint">{r.sector}</td>
                        <td className="py-3 pl-4 text-right font-mono tabular-nums text-ink">{formatCurrency(r.price)}</td>
                        <td className={`py-3 pl-4 text-right font-mono tabular-nums ${r.change_percent === null ? "text-ink-faint" : positive ? "text-positive" : "text-negative"}`}>
                          {r.change_percent === null ? "N/A" : formatPercent(r.change_percent)}
                        </td>
                        <td className="py-3 pl-4 text-right font-mono tabular-nums text-ink-muted">{formatLargeCurrency(r.market_cap)}</td>
                        <td className="py-3 pl-4 text-right font-mono tabular-nums text-ink-muted">{r.pe_ratio?.toFixed(1) ?? "N/A"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Panel>
          )}
        </>
      )}

      {!hasSearched && !loading && (
        <p className="text-sm text-ink-faint">Set your filters and run a screen to see matching stocks.</p>
      )}
    </div>
  );
}

function NumberField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <label className="mb-1.5 block text-xs font-medium text-ink-muted">{label}</label>
      <input
        type="number"
        step="any"
        min="0"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Any"
        className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:border-primary focus:outline-none"
      />
    </div>
  );
}
