"use client";

import { useEffect, useRef, useState } from "react";
import type { SearchResult } from "@/lib/types";
import { PUBLIC_API_BASE_URL } from "@/lib/api";

const MAX_TICKERS = 6;

export function TickerMultiSelect({
  tickers,
  onChange,
}: {
  tickers: string[];
  onChange: (tickers: string[]) => void;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.trim().length === 0) return;
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`${PUBLIC_API_BASE_URL}/api/stocks/search?q=${encodeURIComponent(query)}`);
        if (!res.ok) return;
        const data: SearchResult[] = await res.json();
        setResults(data);
        setOpen(true);
      } catch {
        // best-effort convenience feature
      }
    }, 200);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  function addTicker(ticker: string) {
    const upper = ticker.toUpperCase();
    if (tickers.includes(upper) || tickers.length >= MAX_TICKERS) return;
    onChange([...tickers, upper]);
    setQuery("");
    setOpen(false);
  }

  function removeTicker(ticker: string) {
    onChange(tickers.filter((t) => t !== ticker));
  }

  const atLimit = tickers.length >= MAX_TICKERS;

  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-2">
        {tickers.map((t) => (
          <span
            key={t}
            className="flex items-center gap-1.5 rounded-md border border-border bg-surface-sunken px-2 py-1 font-mono text-xs font-medium text-ink"
          >
            {t}
            <button
              type="button"
              onClick={() => removeTicker(t)}
              aria-label={`Remove ${t}`}
              className="text-ink-faint transition-colors duration-[var(--duration-fast)] hover:text-negative"
            >
              ×
            </button>
          </span>
        ))}
      </div>

      <div ref={containerRef} className="relative max-w-sm">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && results[0]) addTicker(results[0].ticker);
          }}
          disabled={atLimit}
          placeholder={atLimit ? `Max ${MAX_TICKERS} tickers` : "Add a ticker to compare"}
          aria-label="Add a ticker to compare"
          className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-faint disabled:cursor-not-allowed disabled:opacity-60 focus:border-primary focus:outline-none"
        />
        {open && results.length > 0 && query.trim().length > 0 && !atLimit && (
          <ul className="animate-dropdown-in origin-top absolute z-30 mt-1.5 w-full overflow-hidden rounded-md border border-border bg-surface shadow-lg">
            {results.map((r) => {
              const alreadyAdded = tickers.includes(r.ticker);
              return (
                <li key={r.ticker}>
                  <button
                    type="button"
                    disabled={alreadyAdded}
                    onClick={() => addTicker(r.ticker)}
                    className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm transition-colors duration-[var(--duration-fast)] hover:bg-surface-sunken disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <span className="flex items-baseline gap-2 truncate">
                      <span className="font-mono font-medium text-ink">{r.ticker}</span>
                      <span className="truncate text-ink-muted">{r.name}</span>
                    </span>
                    {alreadyAdded && <span className="shrink-0 text-xs text-ink-faint">Added</span>}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
