"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";
import { watchlistApi, ApiError } from "@/lib/api";
import type { WatchlistItemOut } from "@/lib/types";
import { formatCurrency, formatPercent } from "@/lib/format";
import { Panel } from "@/components/ui/Panel";
import { Button } from "@/components/ui/Button";
import { PulseBlock } from "@/components/dashboard/Skeletons";
import { DataSourceBanner } from "@/components/dashboard/DataSourceBanner";

export function WatchlistView() {
  const { token } = useAuth();
  const [items, setItems] = useState<WatchlistItemOut[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [addTicker, setAddTicker] = useState("");
  const [adding, setAdding] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);

  async function refresh() {
    if (!token) return;
    try {
      const data = await watchlistApi.list(token);
      setItems(data);
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load your watchlist.");
    }
  }

  useEffect(() => {
    if (!token) return;
    // Inlined (rather than calling refresh()) so every setState here is
    // nested inside a .then/.catch, satisfying the lint rule against
    // setState-in-effect — refresh() itself is still used for reloads
    // after add/remove, which aren't inside an effect.
    watchlistApi
      .list(token)
      .then((data) => {
        setItems(data);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(err instanceof ApiError ? err.message : "Couldn't load your watchlist.");
      });
  }, [token]);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !addTicker.trim()) return;
    setAdding(true);
    setAddError(null);
    try {
      await watchlistApi.add(token, addTicker.trim());
      setAddTicker("");
      await refresh();
    } catch (err) {
      setAddError(err instanceof ApiError ? err.message : "Couldn't add that ticker.");
    } finally {
      setAdding(false);
    }
  }

  async function handleRemove(ticker: string) {
    if (!token) return;
    setItems((prev) => (prev ? prev.filter((i) => i.ticker !== ticker) : prev));
    try {
      await watchlistApi.remove(token, ticker);
    } catch {
      await refresh(); // roll back the optimistic removal if it actually failed
    }
  }

  const isSynthetic = items?.some((i) => i.is_synthetic) ?? false;

  return (
    <div className="flex flex-col gap-5">
      {isSynthetic && <DataSourceBanner />}

      <Panel title="Add to watchlist">
        <form onSubmit={handleAdd} className="flex flex-wrap items-end gap-3">
          <div className="min-w-[220px] flex-1">
            <label className="mb-1.5 block text-xs font-medium text-ink-muted" htmlFor="add-ticker">
              Ticker
            </label>
            <input
              id="add-ticker"
              value={addTicker}
              onChange={(e) => setAddTicker(e.target.value.toUpperCase())}
              placeholder="e.g. AAPL"
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink placeholder:text-ink-faint focus:border-primary focus:outline-none"
            />
          </div>
          <Button type="submit" loading={adding} disabled={!addTicker.trim()}>
            Add
          </Button>
        </form>
        {addError && (
          <p role="alert" className="mt-2 text-sm text-negative">
            {addError}
          </p>
        )}
      </Panel>

      {error && (
        <div role="alert" className="rounded-lg border border-negative/30 bg-negative-soft px-4 py-3 text-sm text-negative">
          {error}
        </div>
      )}

      {items === null && !error && (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <PulseBlock key={i} className="h-14 w-full" />
          ))}
        </div>
      )}

      {items && items.length === 0 && (
        <p className="text-sm text-ink-faint">Nothing on your watchlist yet — add a ticker above.</p>
      )}

      {items && items.length > 0 && (
        <Panel>
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-ink-faint">
                <th className="py-2 pr-4 font-medium">Ticker</th>
                <th className="py-2 pl-4 text-right font-medium">Price</th>
                <th className="py-2 pl-4 text-right font-medium">Change</th>
                <th className="py-2 pl-4" />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const positive = (item.change ?? 0) >= 0;
                return (
                  <tr key={item.ticker} className="border-b border-border/60">
                    <td className="py-3 pr-4">
                      <Link href={`/research/${item.ticker}`} className="font-mono font-medium text-ink hover:text-primary">
                        {item.ticker}
                      </Link>
                    </td>
                    <td className="py-3 pl-4 text-right font-mono tabular-nums text-ink">
                      {formatCurrency(item.price)}
                    </td>
                    <td
                      className={`py-3 pl-4 text-right font-mono tabular-nums ${
                        item.change === null ? "text-ink-faint" : positive ? "text-positive" : "text-negative"
                      }`}
                    >
                      {item.change_percent === null ? "N/A" : formatPercent(item.change_percent)}
                    </td>
                    <td className="py-3 pl-4 text-right">
                      <button
                        type="button"
                        onClick={() => handleRemove(item.ticker)}
                        className="text-xs text-ink-faint transition-colors duration-[var(--duration-fast)] hover:text-negative"
                      >
                        Remove
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}
