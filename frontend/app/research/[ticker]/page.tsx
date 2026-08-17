import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { api, ApiError } from "@/lib/api";
import { PriceHeader } from "@/components/dashboard/PriceHeader";
import { ResearchDashboard } from "@/components/dashboard/ResearchDashboard";

export async function generateMetadata({ params }: { params: Promise<{ ticker: string }> }): Promise<Metadata> {
  const { ticker } = await params;
  return {
    title: `${ticker.toUpperCase()} · Stock Research & Analytics`,
  };
}

export default async function ResearchPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = await params;

  let overview;
  try {
    overview = await api.getOverview(ticker);
  } catch (err) {
    if (err instanceof ApiError && err.status === 400) {
      notFound();
    }
    return (
      <div className="mx-auto w-full max-w-[1400px] px-4 py-10 sm:px-6">
        <div role="alert" className="rounded-lg border border-negative/30 bg-negative-soft px-4 py-3 text-sm text-negative">
          Couldn&apos;t load data for {ticker.toUpperCase()} right now. The data source may be temporarily
          unavailable — try again in a moment.
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      <div className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6">
        <div className="mb-6 border-b border-border pb-6">
          <PriceHeader overview={overview} />
        </div>
        <ResearchDashboard ticker={overview.ticker} />
      </div>
    </div>
  );
}
