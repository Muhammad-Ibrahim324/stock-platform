import type { DividendsResponse } from "@/lib/types";
import { formatCurrency, formatDate, formatPercent } from "@/lib/format";
import { Panel } from "@/components/ui/Panel";

export function DividendsPanel({ dividends }: { dividends: DividendsResponse }) {
  const recent = [...dividends.payments].reverse().slice(0, 8);

  return (
    <Panel title="Dividends">
      <div className="mb-5 grid grid-cols-2 gap-4 sm:grid-cols-3">
        <div>
          <p className="text-xs text-ink-faint">Trailing yield</p>
          <p className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-ink">
            {formatPercent(dividends.dividend_yield === null ? null : dividends.dividend_yield * 100, { showSign: false })}
          </p>
        </div>
        <div>
          <p className="text-xs text-ink-faint">Annual rate</p>
          <p className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-ink">
            {formatCurrency(dividends.trailing_annual_dividend_rate)}
          </p>
        </div>
      </div>

      {recent.length === 0 ? (
        <p className="text-sm text-ink-faint">
          {dividends.is_synthetic
            ? "Dividend history isn't available in demo mode."
            : "No dividend payments on record — this ticker may not pay a dividend."}
        </p>
      ) : (
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-ink-faint">
              <th className="py-2 pr-4 font-medium">Ex-dividend date</th>
              <th className="py-2 pl-4 text-right font-medium">Amount</th>
            </tr>
          </thead>
          <tbody>
            {recent.map((p) => (
              <tr key={p.ex_date} className="border-b border-border/60">
                <td className="py-2 pr-4 text-ink-muted">{formatDate(p.ex_date)}</td>
                <td className="py-2 pl-4 text-right font-mono tabular-nums text-ink">{formatCurrency(p.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  );
}
