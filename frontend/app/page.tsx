import Link from "next/link";
import { Button } from "@/components/ui/Button";

const FEATURES = [
  {
    title: "Research",
    description: "Price history, technicals, returns, and risk metrics for any ticker — real math, shown plainly.",
    href: "/research/AAPL",
    cta: "Explore AAPL",
  },
  {
    title: "Compare",
    description: "Overlay normalized returns and correlation across up to six tickers at once.",
    href: "/compare",
    cta: "Compare stocks",
  },
  {
    title: "Screener",
    description: "Filter by sector, market cap, valuation, and yield across a bundled universe of ~280 tickers.",
    href: "/screener",
    cta: "Run a screen",
  },
  {
    title: "Portfolio",
    description: "Track holdings, see allocation and gain/loss, and get a real (labeled) risk read on your mix.",
    href: "/signup",
    cta: "Track a portfolio",
  },
];

export default function Home() {
  return (
    <div className="flex flex-1 flex-col">
      <section className="border-b border-border bg-surface">
        <div className="mx-auto max-w-[1000px] px-4 py-20 text-center sm:px-6 sm:py-28">
          <h1 className="font-display text-4xl font-semibold leading-[1.1] tracking-tight text-ink sm:text-5xl">
            See the numbers behind the ticker.
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-base leading-relaxed text-ink-muted sm:text-lg">
            Returns, risk, and technicals computed properly — Sharpe, Sortino, drawdown, VaR — not just a
            price chart with a headline stapled to it. Free, and educational only.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/research/AAPL">
              <Button size="md" className="px-6 py-2.5 text-[15px]">
                Start researching
              </Button>
            </Link>
            <Link href="/signup">
              <Button variant="secondary" size="md" className="px-6 py-2.5 text-[15px]">
                Create a free account
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto w-full max-w-[1200px] px-4 py-14 sm:px-6">
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {FEATURES.map((f) => (
            <Link
              key={f.title}
              href={f.href}
              className="group flex flex-col rounded-lg border border-border bg-surface p-5 transition-colors duration-[var(--duration-fast)] hover:border-border-strong"
            >
              <h2 className="font-display text-base font-semibold text-ink">{f.title}</h2>
              <p className="mt-2 flex-1 text-sm leading-relaxed text-ink-muted">{f.description}</p>
              <span className="mt-4 text-sm font-medium text-primary transition-transform duration-[var(--duration-fast)] group-hover:translate-x-0.5">
                {f.cta} →
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="border-t border-border bg-surface-sunken">
        <div className="mx-auto max-w-[1000px] px-4 py-10 text-center sm:px-6">
          <p className="text-sm text-ink-muted">
            Educational and research use only. This platform does not provide investment advice, and prices
            shown may be illustrative demo data — every screen discloses which.
          </p>
        </div>
      </section>
    </div>
  );
}
