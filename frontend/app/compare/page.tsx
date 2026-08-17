import type { Metadata } from "next";
import { ComparisonView } from "@/components/compare/ComparisonView";

export const metadata: Metadata = {
  title: "Compare · Stock Research & Analytics",
};

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ tickers?: string }>;
}) {
  const { tickers } = await searchParams;
  const initialTickers = tickers
    ? tickers
        .split(",")
        .map((t) => t.trim().toUpperCase())
        .filter(Boolean)
        .slice(0, 6)
    : ["AAPL", "MSFT", "GOOGL"];

  return (
    <div className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6">
      <div className="mb-6 border-b border-border pb-6">
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Compare</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Overlay normalized returns and correlations across up to 6 tickers.
        </p>
      </div>
      <ComparisonView initialTickers={initialTickers} />
    </div>
  );
}
