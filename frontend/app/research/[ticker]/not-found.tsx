import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto flex w-full max-w-[1400px] flex-1 flex-col items-center justify-center gap-3 px-4 py-24 text-center sm:px-6">
      <h1 className="font-display text-xl font-semibold text-ink">That doesn&apos;t look like a valid ticker</h1>
      <p className="max-w-sm text-sm text-ink-muted">
        Try searching for a company or symbol above, or head back to a known ticker.
      </p>
      <Link href="/research/AAPL" className="mt-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-ink-inverse transition-colors duration-[var(--duration-fast)] hover:bg-primary-hover">
        Go to AAPL
      </Link>
    </div>
  );
}
