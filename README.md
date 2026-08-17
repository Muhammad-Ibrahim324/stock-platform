# Stock Market Research & Analytics Platform

A research and analytics tool for exploring stock price history, returns,
risk, and technical indicators. FastAPI backend, Next.js frontend.

This is educational software. Nothing in this repository or the app it
builds is investment advice.

## Status

This is Phase 1 through 5 of a larger PRD (`PRD__Stock_Market_Research___Analytics_Platform.md`) — every phase in the original roadmap is now built. What's working:

- Full user accounts, watchlist, portfolio tracking with real cost-basis
  math and reused risk analytics, a stock screener
- Company overview, price history, technical indicators, returns, risk
  (Sharpe/Sortino/drawdown/VaR/CVaR/beta), fundamentals, financial
  statements, dividends, multi-stock comparison
- **Forecasting** — a ridge regression baseline evaluated walk-forward
  (never trained on data from after the day it predicted), scored
  honestly against a naive baseline rather than presented as reliable
- **Backtesting** — SMA crossover, RSI mean-reversion, and buy-and-hold
  strategies with transaction costs and slippage, scored with the same
  Sharpe/Sortino/drawdown functions used everywhere else in the app
- ~280-ticker universe, a real landing page, login/signup

Not built: dark mode. See `docs/ROADMAP.md`.

## On forecasting and backtesting specifically

Read this before the numbers, not after. The forecasting model is a
simple baseline (ridge regression on lagged returns + technical
indicators) evaluated walk-forward — see
`backend/app/analytics/forecasting.py` for exactly what that means and
why it matters. It does not reliably predict price movements, and the
API reports honestly when it fails to beat a trivial "predict no change"
baseline, which is the normal outcome for daily equity returns, not a
bug. The backtester (`backend/app/analytics/backtesting.py`) simulates
simple rules-based strategies against historical prices with costs
included; backtested performance on historical data does not predict
future results, especially for a strategy whose parameters were tuned by
trying a few values (a form of implicit curve-fitting). Both endpoints
carry this disclaimer in their responses, not just in this README.

## Accounts & data

Signing up creates a real account (hashed password, JWT session) stored in
a local database — by default SQLite (`backend/stock_platform.db`), no
setup required. Point `DATABASE_URL` at Postgres for production; every
model is plain SQLAlchemy, so that's a config change, not a code change.
There's no email verification or password reset flow — see
`backend/app/core/security.py` for exactly what's in and out of scope.

## Why prices might say "demo data"

The default data source is [yfinance](https://github.com/ranaroussi/yfinance),
which needs outbound internet access and requires no API key. If it can't
reach Yahoo Finance — no network access, rate limiting, an unrecognized
ticker — the backend fails over to a seeded synthetic price generator rather
than erroring out. Every response carries an `is_synthetic` flag, and the
frontend shows a visible banner whenever it's set. Demo data is never
presented as real, and fundamentals are never fabricated: in demo mode they
come back as `null` / "N/A" instead of plausible-looking fake numbers.

Set `ENABLE_SYNTHETIC_FALLBACK=false` in `backend/.env` if you'd rather the
API return a clean error than ever serve demo data.

## Tech stack

- **Backend:** FastAPI, Pandas/NumPy for the analytics, Pydantic for
  schemas, yfinance for market data, pytest for tests
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS v4, Recharts
- **Fonts:** IBM Plex Sans/Mono, Space Grotesk (self-hosted via
  `@fontsource`, no runtime dependency on Google's font CDN)

## Running it

### Docker (recommended)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Frontend: http://localhost:3000
Backend docs: http://localhost:8000/docs

### Without Docker

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Tests

```bash
cd backend
pytest -v
```

132 tests, including a dedicated no-lookahead regression test for the
forecasting walk-forward loop (mutates future rows and asserts past
predictions don't change) and for the backtester's cost accounting.

## Architecture

```
backend/app/
  data/providers/     # MarketDataProvider interface + yfinance & synthetic implementations
  data/service.py      # caching, failover, ticker validation
  analytics/           # pure functions: returns, risk, technical indicators
  api/routes/          # FastAPI routes composing data + analytics into responses

frontend/
  app/research/[ticker]/   # the research page (server-rendered overview + client dashboard)
  components/dashboard/    # chart panels (price, returns, risk, technicals)
  lib/                     # typed API client, formatting helpers
```

The data layer is provider-agnostic by design: `MarketDataProvider` is an
abstract interface, and swapping in a paid provider (Alpha Vantage,
Financial Modeling Prep, Polygon) means implementing that interface once —
nothing in the analytics or API layers needs to change.

## Methodology notes

- All annualized figures assume 252 trading days/year.
- RSI uses Wilder's smoothing (the standard definition — a plain
  rolling-mean RSI is a common shortcut that gives different numbers).
- Sharpe/Sortino use a configurable annualized risk-free rate, default 4%.
- VaR/CVaR are historical (non-parametric), not assumed-normal.
- Every indicator/return/risk function only ever looks at data up to the
  current row — no look-ahead — which matters once this feeds a
  backtester or forecaster in a later phase.

Full formulas are documented inline in `backend/app/analytics/`.

## Known limitations

- Ticker search/autocomplete and the screener both draw from the same
  bundled ~280-ticker directory (`backend/app/data/ticker_directory.py`),
  not a live market-wide feed. The screener scans a bounded slice of
  candidates per request (see `candidate_limit` in its response) since
  there's no bulk screening API to query instead — narrow by sector or
  raise the limit for a wider (slower) scan.
- Financial statement line-item labels come straight from the provider,
  unnormalized (see `backend/app/data/schemas.py::StatementLineItem`) —
  real companies don't report perfectly consistent row labels, and
  force-mapping them into a rigid schema risks silently mislabeling data.
- Portfolio risk metrics are a hypothetical ("how would today's mix of
  holdings have behaved over the trailing period"), not your realized
  return history — the app says this explicitly in the risk panel, since
  positions were presumably bought at different times.
- No email verification or password reset — see the security module.
- No dark mode yet. The design tokens are structured to support it, it's
  just not implemented.
- No screenshots in this README yet.

## UI/UX audit pass

The frontend motion system got an actual audit, not a vibe check. Recon
swept every `transition`/`hover`/`animate` site in the codebase, findings
were logged with severity, and fixes were applied and re-verified:

- **Fixed:** `Button` used `transition-all` (animates every property,
  not just the ones that change) — scoped to the actual properties.
- **Fixed:** three popovers (ticker search results, the account menu, the
  compare-page ticker picker) appeared with zero transition — added a
  scale+fade entrance anchored at the trigger edge (`origin-top` /
  `origin-top-right`, never center — a menu grows from where it came
  from).
- **Fixed:** no `prefers-reduced-motion` handling anywhere — added a
  global override that keeps color/opacity transitions (removing them
  makes state changes harder to follow) but zeroes out movement.
- **Fixed:** 15 sites used `transition-colors` without an explicit
  duration, silently falling back to Tailwind's default instead of the
  app's own `--duration-fast` token.
- **Fixed:** every chart had animation disabled, including the primary
  price chart, which is seen once per ticker view — enabled a 450ms
  entrance draw-in there specifically; left the denser secondary charts
  (RSI/MACD, forecast, backtest, compare) crisp and static on purpose.

**Not fixed, flagged honestly:** hover states aren't gated behind
`@media (hover: hover)`, so a touch device that fires a synthetic hover
could see a transition meant for a mouse. In practice modern mobile
browsers clear `:hover` quickly, but it's not compliant with the letter
of the standard, and retrofitting ~30 call sites was out of scope for
this pass. The price chart's 450ms entrance also exceeds the sub-300ms
budget generally recommended for interactive UI elements — the
justification is that it's a content reveal rather than a button/toggle
response, but that's a judgment call worth someone else's opinion too.

## License

MIT — see `LICENSE`.
