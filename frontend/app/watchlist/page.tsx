import type { Metadata } from "next";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { WatchlistView } from "@/components/watchlist/WatchlistView";

export const metadata: Metadata = {
  title: "Watchlist · Stock Research & Analytics",
};

export default function WatchlistPage() {
  return (
    <div className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6">
      <div className="mb-6 border-b border-border pb-6">
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Watchlist</h1>
        <p className="mt-1 text-sm text-ink-muted">Keep an eye on tickers without opening each one.</p>
      </div>
      <RequireAuth title="Watchlist">
        <WatchlistView />
      </RequireAuth>
    </div>
  );
}
