export function SiteFooter() {
  return (
    <footer className="border-t border-border bg-surface">
      <div className="mx-auto max-w-[1400px] px-4 py-6 text-xs leading-relaxed text-ink-faint sm:px-6">
        <p className="max-w-3xl">
          This platform is for educational and research purposes only. Nothing here is
          financial, investment, or trading advice, and no output — including forecasts or
          model-generated figures — should be relied on to make investment decisions.
          Market data may be delayed, incomplete, or, where noted, illustrative synthetic
          data rather than real prices. Past performance does not indicate future results.
        </p>
        <p className="mt-2">Built with the FastAPI + Next.js stack outlined in the project README.</p>
      </div>
    </footer>
  );
}
