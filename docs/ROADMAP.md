# Roadmap

Tracking progress against `PRD__Stock_Market_Research___Analytics_Platform.md`.
Phases follow the PRD's own MVP priority order (§49).

## Phase 1 — Core (done)

- [x] Data provider abstraction (`yfinance` + synthetic fallback, honest failover)
- [x] Company overview endpoint
- [x] Price history + range selector
- [x] Technical indicators: SMA, EMA, RSI, MACD, Bollinger, ATR, ADX, hist. vol
- [x] Returns: total/annualized, growth-of-investment, daily distribution
- [x] Risk: volatility, Sharpe, Sortino, max/current drawdown, VaR/CVaR, beta, correlation
- [x] Ticker search/autocomplete (static directory)
- [x] Design system (tokens, typography, restrained institutional palette)
- [x] Docker Compose, README, tests (43 passing)

## Phase 2 — Comparison & fundamentals (done)

- [x] Multi-stock overlay comparison (normalized % change, up to 6 tickers)
- [x] Correlation matrix across compared tickers
- [x] Fundamentals display panel (valuation, profitability, health ratios)
- [x] Financial statements (income statement, balance sheet, cash flow),
      annual and quarterly, with N/A rather than fabricated gaps
- [x] Dividend history and trailing yield

## Phase 3 — Screener, watchlist, accounts & portfolio (done)

- [x] Full user accounts (bcrypt + JWT, real database)
- [x] Watchlist (per-user, live quotes)
- [x] Portfolio tracking: holdings CRUD, exact cost-basis/gain-loss math,
      allocation by ticker/sector, portfolio-level risk (reusing the
      existing Sharpe/Sortino/drawdown functions)
- [x] Stock screener (bounded-scan design — see README limitations)
- [x] Expanded ticker universe (~280 tickers across every major sector)
- [x] Landing page, login/signup pages, auth-aware nav

## Phase 4 — Portfolio tools (done — folded into Phase 3)

Portfolio construction/tracking and portfolio-level risk/return analytics
shipped as part of Phase 3 above, since the account system needed to exist
for either watchlist or portfolio to make sense, and both were natural to
build together once auth was in place.

- [ ] Efficient frontier / mean-variance optimization (not yet — this is
      the one piece of original Phase 4 scope still open)
- [ ] Rebalancing suggestions

## Phase 5 — Forecasting & backtesting (done)

- [x] Feature pipeline built on the existing no-lookahead indicator functions
- [x] Baseline forecasting model (ridge regression) with walk-forward validation
- [x] Backtesting engine with transaction costs and slippage
      (SMA crossover, RSI mean-reversion, buy-and-hold)
- [x] Honest model performance reporting — scored against naive baselines,
      framed as "not investment advice" in both the API response and the UI

## Cross-cutting, not tied to one phase

- [x] Auth (done as part of Phase 3)
- [x] UI/UX motion audit (done — see README "UI/UX audit pass"; one
      item — hover states not gated behind `(hover: hover)` — flagged
      but not fixed)
- [ ] Dark mode
- [ ] Live ticker search / screener API (swap the static directory for
      Alpha Vantage `SYMBOL_SEARCH` or FMP's screener endpoint)
- [ ] Screenshots / demo GIF in the README
- [ ] CI (GitHub Actions running `pytest` + `npm run build` + `npm run lint`)
- [ ] Rate limiting backed by Redis instead of the in-process limiter,
      once this runs as more than one backend instance
- [ ] Alembic migrations (schema is currently created via `create_all` on
      startup — fine for a fresh deploy, not for evolving one in place)
- [ ] Hover states gated behind `@media (hover: hover) and (pointer: fine)`
      (flagged in the UI/UX audit, not yet fixed — ~30 call sites)

## Design skills applied so far, and where the rest come in

`frontend-design`, `ui-ux-pro-max`, `emil-design-eng`, and `apple-design`
shaped the Phase 1 design system and component decisions (typography
pairing, verified-contrast palette, restrained motion tokens, the "Panel"
primitive instead of stacking generic cards).

`find-animation-opportunities`, `improve-animations`, `review-animations`,
and `animation-vocabulary` are audit tools that need real, running UI with
actual animations to critique — they're most useful once Phase 2+ adds more
interaction (comparison overlays, screener filtering, portfolio charts) for
them to review. Worth a dedicated pass once there's more surface area than
one dashboard page.

`graphify` is a good fit for generating an architecture/dependency diagram
once the codebase is bigger than Phase 1 — most valuable after Phase 2 or 3,
when there's enough cross-module structure for a knowledge graph to add
value over just reading the directory tree.

`llm-council` was used for the Phase 1 data-layer architecture decision
(see the PR/commit notes); worth another pass for the Phase 4/5 decisions
that carry real modeling risk (which optimization approach, which
forecasting baseline, how to frame model output so it doesn't read as
advice).
