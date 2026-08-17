"use client";

import { useEffect, useMemo, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type {
  DividendsResponse,
  FundamentalsResponse,
  Period,
  PriceHistoryResponse,
  ReturnsResponse,
  RiskResponse,
  TechnicalsResponse,
} from "@/lib/types";
import { RangeSelector } from "./RangeSelector";
import { PriceChart, type PriceChartPoint } from "./PriceChart";
import { ReturnsPanel } from "./ReturnsPanel";
import { RiskPanel } from "./RiskPanel";
import { TechnicalsPanel } from "./TechnicalsPanel";
import { FundamentalsPanel } from "./FundamentalsPanel";
import { DividendsPanel } from "./DividendsPanel";
import { FinancialStatementsPanel } from "./FinancialStatementsPanel";
import { ForecastPanel } from "./ForecastPanel";
import { BacktestPanel } from "./BacktestPanel";
import { DataSourceBanner } from "./DataSourceBanner";
import { ChartPanelSkeleton, MetricGridSkeleton } from "./Skeletons";
import { Panel } from "@/components/ui/Panel";

interface DashboardData {
  prices: PriceHistoryResponse;
  technicals: TechnicalsResponse;
  returns: ReturnsResponse;
  risk: RiskResponse;
}

interface ExtrasData {
  fundamentals: FundamentalsResponse;
  dividends: DividendsResponse;
}

export function ResearchDashboard({ ticker }: { ticker: string }) {
  const [period, setPeriod] = useState<Period>("1y");
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  // The ticker+period that `data`/`error` actually correspond to. Comparing
  // this against the current ticker/period derives "loading" without ever
  // needing a synchronous setState(true) at the top of the effect below.
  const [settledKey, setSettledKey] = useState<string | null>(null);

  const requestKey = `${ticker}:${period}`;
  const loading = settledKey !== requestKey;

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      api.getPrices(ticker, period),
      api.getTechnicals(ticker, period),
      api.getReturns(ticker, period),
      api.getRisk(ticker, period, "SPY"),
    ])
      .then(([prices, technicals, returns, risk]) => {
        if (cancelled) return;
        setData({ prices, technicals, returns, risk });
        setError(null);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message =
          err instanceof ApiError
            ? err.message
            : "Something went wrong loading this data. Please try again.";
        setError(message);
      })
      .finally(() => {
        if (!cancelled) setSettledKey(requestKey);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- requestKey is derived from ticker/period
  }, [ticker, period]);

  // Fundamentals/dividends don't depend on the selected range, so they get
  // their own effect keyed only on ticker — switching ranges shouldn't
  // re-fetch them.
  const [extras, setExtras] = useState<ExtrasData | null>(null);
  const [extrasSettledTicker, setExtrasSettledTicker] = useState<string | null>(null);
  const extrasLoading = extrasSettledTicker !== ticker;

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.getFundamentals(ticker), api.getDividends(ticker)])
      .then(([fundamentals, dividends]) => {
        if (cancelled) return;
        setExtras({ fundamentals, dividends });
      })
      .catch(() => {
        if (cancelled) return;
        setExtras(null);
      })
      .finally(() => {
        if (!cancelled) setExtrasSettledTicker(ticker);
      });
    return () => {
      cancelled = true;
    };
  }, [ticker]);

  const chartData: PriceChartPoint[] = useMemo(() => {
    if (!data) return [];
    const smaByDate = new Map(data.technicals.points.map((p) => [p.trade_date, p]));
    return data.prices.bars.map((bar) => {
      const indicator = smaByDate.get(bar.trade_date);
      return {
        trade_date: bar.trade_date,
        close: bar.adj_close,
        sma_20: indicator?.sma_20 ?? null,
        sma_50: indicator?.sma_50 ?? null,
      };
    });
  }, [data]);

  const isSynthetic = data
    ? data.prices.is_synthetic || data.technicals.is_synthetic || data.returns.is_synthetic || data.risk.is_synthetic
    : false;

  const periodIsPositive = data ? data.returns.total_return_pct >= 0 : true;

  return (
    <div className="flex flex-col gap-5">
      {isSynthetic && <DataSourceBanner />}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="font-display text-sm font-semibold text-ink-muted">Price history</h2>
        <RangeSelector value={period} onChange={setPeriod} />
      </div>

      {error && (
        <div role="alert" className="rounded-lg border border-negative/30 bg-negative-soft px-4 py-3 text-sm text-negative">
          {error}
        </div>
      )}

      {loading && !data && (
        <div className="flex flex-col gap-5">
          <ChartPanelSkeleton />
          <MetricGridSkeleton />
          <MetricGridSkeleton />
        </div>
      )}

      {data && (
        <div className="flex flex-col gap-5">
          <Panel className="pt-1">
            <PriceChart data={chartData} isPositivePeriod={periodIsPositive} />
          </Panel>

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            <ReturnsPanel returns={data.returns} />
            <RiskPanel risk={data.risk} />
          </div>

          <TechnicalsPanel points={data.technicals.points} />

          <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
            {extrasLoading && !extras && (
              <>
                <MetricGridSkeleton />
                <MetricGridSkeleton />
              </>
            )}
            {extras && (
              <>
                <FundamentalsPanel fundamentals={extras.fundamentals} />
                <DividendsPanel dividends={extras.dividends} />
              </>
            )}
          </div>

          <FinancialStatementsPanel ticker={ticker} />

          <ForecastPanel ticker={ticker} />
          <BacktestPanel ticker={ticker} />
        </div>
      )}
    </div>
  );
}
