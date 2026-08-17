import clsx from "clsx";
import type { OverviewResponse } from "@/lib/types";
import { formatCurrency, formatLargeCurrency, formatPercent } from "@/lib/format";

export function PriceHeader({ overview }: { overview: OverviewResponse }) {
  const positive = overview.change >= 0;
  const week52Range = overview.week52_low !== null && overview.week52_high !== null;
  const week52Position =
    week52Range && overview.week52_high! > overview.week52_low!
      ? ((overview.price - overview.week52_low!) / (overview.week52_high! - overview.week52_low!)) * 100
      : null;

  return (
    <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <div className="flex items-baseline gap-2.5">
          <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">{overview.ticker}</h1>
          {overview.exchange && (
            <span className="rounded border border-border px-1.5 py-0.5 text-[11px] font-medium uppercase tracking-wide text-ink-faint">
              {overview.exchange}
            </span>
          )}
        </div>
        <p className="mt-1 text-sm text-ink-muted">{overview.company_name}</p>
        {overview.sector && (
          <p className="mt-0.5 text-xs text-ink-faint">
            {overview.sector}
            {overview.industry ? ` · ${overview.industry}` : ""}
          </p>
        )}
      </div>

      <div className="flex flex-col items-start gap-2 sm:items-end">
        <div className="flex items-baseline gap-2.5">
          <span className="font-mono text-3xl font-semibold tabular-nums text-ink">
            {formatCurrency(overview.price)}
          </span>
          <span
            className={clsx(
              "flex items-center gap-1 rounded-md px-2 py-0.5 font-mono text-sm font-medium tabular-nums",
              positive ? "bg-positive-soft text-positive" : "bg-negative-soft text-negative"
            )}
          >
            {positive ? "▲" : "▼"} {formatCurrency(Math.abs(overview.change))} ({formatPercent(overview.change_percent)})
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-xs text-ink-faint">
          {overview.market_cap !== null && (
            <span>
              Mkt Cap <span className="font-mono text-ink-muted">{formatLargeCurrency(overview.market_cap)}</span>
            </span>
          )}
          {week52Range && (
            <span className="flex items-center gap-1.5">
              52W
              <span className="font-mono text-ink-muted">
                {formatCurrency(overview.week52_low)} – {formatCurrency(overview.week52_high)}
              </span>
              {week52Position !== null && (
                <span className="relative h-1 w-14 rounded-full bg-surface-sunken">
                  <span
                    className="absolute top-1/2 h-2 w-2 -translate-y-1/2 -translate-x-1/2 rounded-full bg-primary"
                    style={{ left: `${Math.min(100, Math.max(0, week52Position))}%` }}
                  />
                </span>
              )}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
