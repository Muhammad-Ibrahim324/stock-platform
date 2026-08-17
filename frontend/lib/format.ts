export function formatCurrency(value: number | null | undefined, opts: { decimals?: number } = {}): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  const decimals = opts.decimals ?? (Math.abs(value) < 10 ? 2 : 2);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatPercent(value: number | null | undefined, opts: { decimals?: number; showSign?: boolean } = {}): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  const decimals = opts.decimals ?? 2;
  const sign = opts.showSign !== false && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(decimals)}%`;
}

export function formatNumber(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatCompactNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatLargeCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  return `$${formatCompactNumber(value)}`;
}

export function formatDate(isoDate: string, opts: Intl.DateTimeFormatOptions = {}): string {
  const date = new Date(`${isoDate}T00:00:00`);
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", ...opts }).format(date);
}

export function formatShortDate(isoDate: string): string {
  const date = new Date(`${isoDate}T00:00:00`);
  return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(date);
}

export function isPositive(value: number): boolean {
  return value >= 0;
}
