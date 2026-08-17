export function PulseBlock({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-surface-sunken ${className}`} />;
}

export function ChartPanelSkeleton({ height = "h-72" }: { height?: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4 sm:p-5">
      <PulseBlock className="mb-4 h-4 w-32" />
      <PulseBlock className={`w-full ${height}`} />
    </div>
  );
}

export function MetricGridSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-surface p-4 sm:p-5">
      <PulseBlock className="mb-4 h-4 w-24" />
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i}>
            <PulseBlock className="mb-1.5 h-3 w-16" />
            <PulseBlock className="h-5 w-12" />
          </div>
        ))}
      </div>
    </div>
  );
}
