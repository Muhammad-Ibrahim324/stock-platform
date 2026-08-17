import type { Metadata } from "next";
import { RequireAuth } from "@/components/auth/RequireAuth";
import { PortfolioView } from "@/components/portfolio/PortfolioView";

export const metadata: Metadata = {
  title: "Portfolio · Stock Research & Analytics",
};

export default function PortfolioPage() {
  return (
    <div className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6">
      <div className="mb-6 border-b border-border pb-6">
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink">Portfolio</h1>
        <p className="mt-1 text-sm text-ink-muted">Track holdings, allocation, and risk in one place.</p>
      </div>
      <RequireAuth title="Portfolio">
        <PortfolioView />
      </RequireAuth>
    </div>
  );
}
