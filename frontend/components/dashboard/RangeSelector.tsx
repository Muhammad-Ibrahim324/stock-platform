"use client";

import clsx from "clsx";
import type { Period } from "@/lib/types";

const RANGES: { value: Period; label: string }[] = [
  { value: "5d", label: "5D" },
  { value: "1mo", label: "1M" },
  { value: "3mo", label: "3M" },
  { value: "6mo", label: "6M" },
  { value: "ytd", label: "YTD" },
  { value: "1y", label: "1Y" },
  { value: "5y", label: "5Y" },
  { value: "max", label: "Max" },
];

export function RangeSelector({ value, onChange }: { value: Period; onChange: (p: Period) => void }) {
  return (
    <div role="group" aria-label="Select time range" className="flex items-center gap-0.5 rounded-md bg-surface-sunken p-0.5">
      {RANGES.map((r) => (
        <button
          key={r.value}
          type="button"
          onClick={() => onChange(r.value)}
          aria-pressed={value === r.value}
          className={clsx(
            "rounded px-2.5 py-1 text-xs font-medium transition-colors duration-[var(--duration-fast)]",
            value === r.value ? "bg-surface text-ink shadow-sm" : "text-ink-faint hover:text-ink-muted"
          )}
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}
