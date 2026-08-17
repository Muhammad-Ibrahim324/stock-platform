function cellColor(value: number): string {
  // Diverging scale: strong negative -> negative color, strong positive -> primary color,
  // near zero -> neutral surface. Opacity carries magnitude.
  if (value >= 0) {
    const alpha = Math.min(1, value) * 0.85;
    return `color-mix(in srgb, var(--color-primary) ${(alpha * 100).toFixed(0)}%, var(--color-surface))`;
  }
  const alpha = Math.min(1, Math.abs(value)) * 0.85;
  return `color-mix(in srgb, var(--color-negative) ${(alpha * 100).toFixed(0)}%, var(--color-surface))`;
}

function textColor(value: number): string {
  return Math.abs(value) > 0.45 ? "var(--color-ink-inverse)" : "var(--color-ink)";
}

export function CorrelationMatrix({ tickers, matrix }: { tickers: string[]; matrix: Record<string, Record<string, number>> }) {
  if (tickers.length < 2) {
    return <p className="text-sm text-ink-faint">Add at least two tickers to see correlations.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="border-collapse text-xs">
        <thead>
          <tr>
            <th className="p-2" />
            {tickers.map((t) => (
              <th key={t} className="p-2 text-center font-mono font-medium text-ink-muted">
                {t}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tickers.map((rowTicker) => (
            <tr key={rowTicker}>
              <th className="p-2 text-right font-mono font-medium text-ink-muted">{rowTicker}</th>
              {tickers.map((colTicker) => {
                const value = matrix[rowTicker]?.[colTicker] ?? 0;
                return (
                  <td key={colTicker} className="p-0.5">
                    <div
                      className="flex h-11 w-14 items-center justify-center rounded font-mono tabular-nums"
                      style={{ background: cellColor(value), color: textColor(value) }}
                      title={`${rowTicker} vs ${colTicker}: ${value.toFixed(2)}`}
                    >
                      {value.toFixed(2)}
                    </div>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
