"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { CompareResponse, Period } from "@/lib/types";
import { TickerMultiSelect } from "./TickerMultiSelect";
import { ComparisonChart } from "./ComparisonChart";
import { CorrelationMatrix } from "./CorrelationMatrix";
import { RangeSelector } from "@/components/dashboard/RangeSelector";
import { DataSourceBanner } from "@/components/dashboard/DataSourceBanner";
import { ChartPanelSkeleton } from "@/components/dashboard/Skeletons";
import { Panel } from "@/components/ui/Panel";
import { formatNumber, formatPercent } from "@/lib/format";

export function ComparisonView({ initialTickers }: { initialTickers: string[] }) {
  const router = useRouter();
  const pathname = usePathname();
  const [tickers, setTickers] = useState<string[]>(initialTickers);
  const [period, setPeriod] = useState<Period>("1y");
  const [data, setData] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [settledKey, setSettledKey] = useState<string | null>(null);

  const requestKey = `${tickers.join(",")}:${period}`;
  const loading = tickers.length > 0 && settledKey !== requestKey;

  useEffect(() => {
    router.replace(tickers.length > 0 ? `${pathname}?tickers=${tickers.join(",")}` : pathname, { scroll: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only sync the URL when the ticker selection itself changes
  }, [tickers]);

  useEffect(() => {
    if (tickers.length === 0) return;
    let cancelled = false;
    api
      .compare(tickers, period)
      .then((res) => {
        if (cancelled) return;
        setData(res);
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : "Couldn't load the comparison right now.");
      })
      .finally(() => {
        if (!cancelled) setSettledKey(requestKey);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- requestKey is derived from tickers/period
  }, [tickers, period]);

  const isSynthetic = data ? data.series.some((s) => s.is_synthetic) : false;
  const hasResults = tickers.length > 0 && data && data.series.length > 0;

  return (
    <div className="flex flex-col gap-5">
      {isSynthetic && <DataSourceBanner />}

      <Panel>
        <TickerMultiSelect tickers={tickers} onChange={setTickers} />
      </Panel>

      {tickers.length === 0 && (
        <p className="text-sm text-ink-faint">Add a ticker above to start comparing.</p>
      )}

      {error && (
        <div role="alert" className="rounded-lg border border-negative/30 bg-negative-soft px-4 py-3 text-sm text-negative">
          {error}
        </div>
      )}

      {loading && <ChartPanelSkeleton height="h-96" />}

      {data && tickers.length > 0 && data.excluded.length > 0 && (
        <div className="rounded-lg border border-accent/30 bg-accent-soft px-4 py-3 text-xs text-ink">
          {data.excluded.map((e) => (
            <p key={e.ticker}>
              <strong className="font-medium">{e.ticker}</strong>: {e.reason}
            </p>
          ))}
        </div>
      )}

      {hasResults && (
        <>
          <Panel title="Normalized return" subtitle="% change from the start of the period">
            <div className="mb-4 flex justify-end">
              <RangeSelector value={period} onChange={setPeriod} />
            </div>
            <ComparisonChart series={data.series} />
          </Panel>

          <Panel title="Summary">
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-border text-left text-xs text-ink-faint">
                  <th className="py-2 pr-4 font-medium">Ticker</th>
                  <th className="py-2 pl-4 text-right font-medium">Total return</th>
                  <th className="py-2 pl-4 text-right font-medium">Volatility (ann.)</th>
                </tr>
              </thead>
              <tbody>
                {data.series.map((s) => (
                  <tr key={s.ticker} className="border-b border-border/60">
                    <td className="py-2 pr-4 font-mono font-medium text-ink">{s.ticker}</td>
                    <td
                      className={`py-2 pl-4 text-right font-mono tabular-nums ${
                        s.total_return_pct >= 0 ? "text-positive" : "text-negative"
                      }`}
                    >
                      {formatPercent(s.total_return_pct)}
                    </td>
                    <td className="py-2 pl-4 text-right font-mono tabular-nums text-ink-muted">
                      {formatNumber(s.annualized_volatility, 1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>

          <Panel title="Correlation" subtitle="Pairwise correlation of daily returns over the selected period">
            <CorrelationMatrix tickers={data.tickers} matrix={data.correlation_matrix} />
          </Panel>
        </>
      )}
    </div>
  );
}
