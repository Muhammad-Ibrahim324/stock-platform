"use client";

import { useEffect, useState } from "react";
import clsx from "clsx";
import { api } from "@/lib/api";
import type { FinancialStatementResponse, StatementFrequency, StatementType } from "@/lib/types";
import { formatCompactNumber, formatShortDate } from "@/lib/format";
import { Panel } from "@/components/ui/Panel";
import { PulseBlock } from "./Skeletons";

const STATEMENT_TABS: { value: StatementType; label: string }[] = [
  { value: "income_statement", label: "Income statement" },
  { value: "balance_sheet", label: "Balance sheet" },
  { value: "cash_flow", label: "Cash flow" },
];

// A handful of line items worth bolding when present — statement row
// labels vary by company/provider (see backend docstring), so this is a
// display nicety, not something the app depends on for correctness.
const HIGHLIGHT_LABELS = new Set([
  "Total Revenue",
  "Net Income",
  "Gross Profit",
  "Operating Income",
  "Total Assets",
  "Total Liabilities Net Minority Interest",
  "Stockholders Equity",
  "Free Cash Flow",
  "Operating Cash Flow",
]);

export function FinancialStatementsPanel({ ticker }: { ticker: string }) {
  const [statementType, setStatementType] = useState<StatementType>("income_statement");
  const [frequency, setFrequency] = useState<StatementFrequency>("annual");
  const [data, setData] = useState<FinancialStatementResponse | null>(null);
  const [settledKey, setSettledKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const requestKey = `${ticker}:${statementType}:${frequency}`;
  const loading = settledKey !== requestKey;

  useEffect(() => {
    let cancelled = false;
    api
      .getFinancials(ticker, statementType, frequency)
      .then((res) => {
        if (cancelled) return;
        setData(res);
        setError(null);
      })
      .catch(() => {
        if (cancelled) return;
        setError("Couldn't load this statement right now.");
      })
      .finally(() => {
        if (!cancelled) setSettledKey(requestKey);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- requestKey is derived from these
  }, [ticker, statementType, frequency]);

  return (
    <Panel title="Financial statements">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1 rounded-md bg-surface-sunken p-0.5">
          {STATEMENT_TABS.map((tab) => (
            <button
              key={tab.value}
              type="button"
              onClick={() => setStatementType(tab.value)}
              aria-pressed={statementType === tab.value}
              className={clsx(
                "rounded px-2.5 py-1 text-xs font-medium transition-colors duration-[var(--duration-fast)]",
                statementType === tab.value ? "bg-surface text-ink shadow-sm" : "text-ink-faint hover:text-ink-muted"
              )}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-1 rounded-md bg-surface-sunken p-0.5">
          {(["annual", "quarterly"] as const).map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFrequency(f)}
              aria-pressed={frequency === f}
              className={clsx(
                "rounded px-2.5 py-1 text-xs font-medium capitalize transition-colors duration-[var(--duration-fast)]",
                frequency === f ? "bg-surface text-ink shadow-sm" : "text-ink-faint hover:text-ink-muted"
              )}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <PulseBlock key={i} className="h-6 w-full" />
          ))}
        </div>
      )}

      {!loading && error && (
        <p role="alert" className="text-sm text-negative">
          {error}
        </p>
      )}

      {!loading && !error && data && data.line_items.length === 0 && (
        <p className="text-sm text-ink-faint">
          {data.is_synthetic
            ? "Statement data isn't available in demo mode — this section stays empty rather than showing invented figures."
            : "No statement data was returned for this ticker."}
        </p>
      )}

      {!loading && !error && data && data.line_items.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[480px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-ink-faint">
                <th className="py-2 pr-4 font-medium">Line item</th>
                {data.periods.map((p) => (
                  <th key={p} className="py-2 pl-4 text-right font-medium">
                    {formatShortDate(p)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.line_items.map((item) => (
                <tr key={item.label} className="border-b border-border/60">
                  <td
                    className={clsx(
                      "py-2 pr-4 text-ink-muted",
                      HIGHLIGHT_LABELS.has(item.label) && "font-medium text-ink"
                    )}
                  >
                    {item.label}
                  </td>
                  {data.periods.map((p) => (
                    <td
                      key={p}
                      className={clsx(
                        "py-2 pl-4 text-right font-mono tabular-nums",
                        HIGHLIGHT_LABELS.has(item.label) ? "font-medium text-ink" : "text-ink-muted"
                      )}
                    >
                      {item.values[p] === null || item.values[p] === undefined
                        ? "N/A"
                        : formatCompactNumber(item.values[p])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Panel>
  );
}
