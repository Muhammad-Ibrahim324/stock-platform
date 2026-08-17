"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import type { SearchResult } from "@/lib/types";
import { PUBLIC_API_BASE_URL } from "@/lib/api";

export function TickerSearch() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [, startTransition] = useTransition();
  const containerRef = useRef<HTMLDivElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (query.trim().length === 0) {
      // Don't clear `results` synchronously here — the dropdown's render
      // condition below also checks the live query length, so stale
      // results simply won't be shown rather than needing to be wiped.
      return;
    }
    debounceRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`${PUBLIC_API_BASE_URL}/api/stocks/search?q=${encodeURIComponent(query)}`);
        if (!res.ok) return;
        const data: SearchResult[] = await res.json();
        setResults(data);
        setOpen(true);
        setActiveIndex(-1);
      } catch {
        // Search is a convenience feature; a transient failure shouldn't be loud.
      }
    }, 200);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query]);

  function go(ticker: string) {
    setOpen(false);
    setQuery("");
    startTransition(() => {
      router.push(`/research/${ticker.toUpperCase()}`);
    });
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (!open || results.length === 0) {
      if (e.key === "Enter" && query.trim()) {
        go(query.trim());
      }
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const chosen = activeIndex >= 0 ? results[activeIndex] : results[0];
      if (chosen) go(chosen.ticker);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div ref={containerRef} className="relative w-full max-w-sm">
      <div className="relative">
        <svg
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint"
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m21 21-4.3-4.3" />
        </svg>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          onKeyDown={onKeyDown}
          placeholder="Search ticker or company"
          aria-label="Search for a stock ticker or company"
          className="w-full rounded-md border border-border bg-surface py-2 pl-9 pr-3 text-sm text-ink placeholder:text-ink-faint transition-colors duration-[var(--duration-fast)] focus:border-primary focus:outline-none"
        />
      </div>

      {open && results.length > 0 && query.trim().length > 0 && (
        <ul
          role="listbox"
          className="animate-dropdown-in origin-top absolute z-30 mt-1.5 w-full overflow-hidden rounded-md border border-border bg-surface shadow-lg"
        >
          {results.map((r, idx) => (
            <li key={r.ticker} role="option" aria-selected={idx === activeIndex}>
              <button
                type="button"
                onMouseEnter={() => setActiveIndex(idx)}
                onClick={() => go(r.ticker)}
                className={`flex w-full items-center justify-between gap-3 px-3 py-2 text-left text-sm transition-colors duration-[var(--duration-fast)] ${
                  idx === activeIndex ? "bg-primary-soft" : "hover:bg-surface-sunken"
                }`}
              >
                <span className="flex items-baseline gap-2 truncate">
                  <span className="font-mono font-medium text-ink">{r.ticker}</span>
                  <span className="truncate text-ink-muted">{r.name}</span>
                </span>
                {r.exchange && <span className="shrink-0 text-xs text-ink-faint">{r.exchange}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
