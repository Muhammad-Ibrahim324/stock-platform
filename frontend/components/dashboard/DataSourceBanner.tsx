export function DataSourceBanner() {
  return (
    <div
      role="status"
      className="flex items-center gap-2.5 border-b border-accent/30 bg-accent-soft px-4 py-2 text-xs text-ink sm:px-6"
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="shrink-0 text-accent">
        <path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
      </svg>
      <span>
        <strong className="font-medium">Demo data.</strong> The live market-data source wasn&apos;t reachable, so
        this view is showing seeded, synthetic prices — not real market data. Figures below are illustrative only.
      </span>
    </div>
  );
}
