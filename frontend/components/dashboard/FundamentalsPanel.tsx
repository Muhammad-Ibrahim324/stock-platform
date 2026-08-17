import type { ReactNode } from "react";
import type { FundamentalsResponse } from "@/lib/types";
import { formatLargeCurrency, formatNumber, formatPercent } from "@/lib/format";
import { Panel } from "@/components/ui/Panel";

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-ink-faint">{label}</p>
      <p className="mt-0.5 font-mono text-sm font-semibold tabular-nums text-ink">{value}</p>
    </div>
  );
}

function Group({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <p className="mb-2.5 text-xs font-semibold uppercase tracking-wide text-ink-faint">{title}</p>
      <div className="grid grid-cols-2 gap-x-4 gap-y-4 sm:grid-cols-3">{children}</div>
    </div>
  );
}

const pct = (v: number | null) => formatPercent(v === null ? null : v * 100, { showSign: false });
const num = (v: number | null) => formatNumber(v);
const usd = (v: number | null) => formatLargeCurrency(v);

export function FundamentalsPanel({ fundamentals }: { fundamentals: FundamentalsResponse }) {
  const allNull = Object.entries(fundamentals).every(
    ([key, v]) => ["ticker", "source", "is_synthetic"].includes(key) || v === null
  );

  return (
    <Panel title="Fundamentals" subtitle="Valuation, profitability, and financial health">
      {allNull ? (
        <p className="text-sm text-ink-faint">
          Fundamentals aren&apos;t available for this ticker right now
          {fundamentals.is_synthetic ? " (demo mode never fabricates these figures)" : ""}.
        </p>
      ) : (
        <div className="flex flex-col gap-6">
          <Group title="Valuation">
            <Metric label="P/E (trailing)" value={num(fundamentals.pe_ratio)} />
            <Metric label="P/E (forward)" value={num(fundamentals.forward_pe)} />
            <Metric label="Price / Sales" value={num(fundamentals.price_to_sales)} />
            <Metric label="Price / Book" value={num(fundamentals.price_to_book)} />
            <Metric label="PEG ratio" value={num(fundamentals.peg_ratio)} />
            <Metric label="EV / EBITDA" value={num(fundamentals.ev_to_ebitda)} />
          </Group>

          <Group title="Profitability">
            <Metric label="Gross margin" value={pct(fundamentals.gross_margin)} />
            <Metric label="Operating margin" value={pct(fundamentals.operating_margin)} />
            <Metric label="Net margin" value={pct(fundamentals.net_margin)} />
            <Metric label="Return on equity" value={pct(fundamentals.return_on_equity)} />
            <Metric label="Return on assets" value={pct(fundamentals.return_on_assets)} />
          </Group>

          <Group title="Financial health">
            <Metric label="Total cash" value={usd(fundamentals.total_cash)} />
            <Metric label="Total debt" value={usd(fundamentals.total_debt)} />
            <Metric label="Debt / Equity" value={num(fundamentals.debt_to_equity)} />
            <Metric label="Current ratio" value={num(fundamentals.current_ratio)} />
            <Metric label="Free cash flow" value={usd(fundamentals.free_cash_flow)} />
          </Group>

          <Group title="Growth (YoY)">
            <Metric label="Revenue growth" value={pct(fundamentals.revenue_growth)} />
            <Metric label="Earnings growth" value={pct(fundamentals.earnings_growth)} />
          </Group>
        </div>
      )}
    </Panel>
  );
}
