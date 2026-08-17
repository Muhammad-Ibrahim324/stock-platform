import type { Metadata } from "next";
import { ScreenerView } from "@/components/screener/ScreenerView";

export const metadata: Metadata = {
  title: "Screener · Stock Research & Analytics",
};

export default function ScreenerPage() {
  return (
    <div className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6">
      <div className="mb-6 border-b border-border pb-6">
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Screener</h1>
        <p className="mt-1 text-sm text-ink-muted">Filter a bundled universe of ~280 well-known tickers.</p>
      </div>
      <ScreenerView />
    </div>
  );
}
