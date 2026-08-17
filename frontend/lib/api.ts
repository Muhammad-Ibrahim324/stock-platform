import type {
  ApiErrorBody,
  BacktestResponse,
  BacktestStrategy,
  CompareResponse,
  DividendsResponse,
  FinancialStatementResponse,
  ForecastResponse,
  FundamentalsResponse,
  HoldingAnalytics,
  HoldingOut,
  OverviewResponse,
  Period,
  PortfolioAnalyticsResponse,
  PriceHistoryResponse,
  ReturnsResponse,
  RiskResponse,
  ScreenerCriteria,
  ScreenerResponse,
  SearchResult,
  StatementFrequency,
  StatementType,
  TechnicalsResponse,
  TokenResponse,
  UserOut,
  WatchlistItemOut,
} from "./types";

const API_BASE_URL =
  typeof window === "undefined"
    ? // Server-side (SSR): when running in Docker Compose, "localhost" from
      // inside the frontend container is the frontend container itself, not
      // the backend — so server components need the internal service
      // hostname. Falls back to the public URL for plain `next dev`.
      process.env.BACKEND_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
    : // Client-side (browser): must be a URL the user's browser can reach.
      (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000");

export const PUBLIC_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function request<T>(path: string, revalidateSeconds?: number, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    next: revalidateSeconds !== undefined ? { revalidate: revalidateSeconds } : undefined,
    cache: revalidateSeconds === undefined ? "no-store" : undefined,
  });

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const body = (await res.json()) as ApiErrorBody;
      if (body?.detail) detail = body.detail;
    } catch {
      // response wasn't JSON — keep the generic message
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function authHeaders(token: string): RequestInit {
  return { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } };
}

function authJson(token: string, body: unknown, method: string): RequestInit {
  return {
    method,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export const api = {
  getOverview: (ticker: string) => request<OverviewResponse>(`/api/stocks/${encodeURIComponent(ticker)}/overview`, 30),

  getPrices: (ticker: string, period: Period = "1y") =>
    request<PriceHistoryResponse>(`/api/stocks/${encodeURIComponent(ticker)}/prices?period=${period}`, 300),

  getTechnicals: (ticker: string, period: Period = "1y") =>
    request<TechnicalsResponse>(`/api/stocks/${encodeURIComponent(ticker)}/technicals?period=${period}`, 300),

  getReturns: (ticker: string, period: Period = "1y", initialInvestment = 10_000) =>
    request<ReturnsResponse>(
      `/api/stocks/${encodeURIComponent(ticker)}/returns?period=${period}&initial_investment=${initialInvestment}`,
      300
    ),

  getRisk: (ticker: string, period: Period = "1y", benchmark?: string, riskFreeRate = 0.04) =>
    request<RiskResponse>(
      `/api/stocks/${encodeURIComponent(ticker)}/risk?period=${period}` +
        (benchmark ? `&benchmark=${encodeURIComponent(benchmark)}` : "") +
        `&risk_free_rate=${riskFreeRate}`,
      300
    ),

  getFundamentals: (ticker: string) =>
    request<FundamentalsResponse>(`/api/stocks/${encodeURIComponent(ticker)}/fundamentals`, 3600),

  getFinancials: (ticker: string, statementType: StatementType, frequency: StatementFrequency = "annual") =>
    request<FinancialStatementResponse>(
      `/api/stocks/${encodeURIComponent(ticker)}/financials/${statementType}?frequency=${frequency}`,
      3600
    ),

  getDividends: (ticker: string) =>
    request<DividendsResponse>(`/api/stocks/${encodeURIComponent(ticker)}/dividends`, 3600),

  compare: (tickers: string[], period: Period = "1y") =>
    request<CompareResponse>(
      `/api/compare?tickers=${encodeURIComponent(tickers.join(","))}&period=${period}`,
      300
    ),

  search: (query: string) => request<SearchResult[]>(`/api/stocks/search?q=${encodeURIComponent(query)}`),

  getForecast: (ticker: string, period: Period = "2y") =>
    request<ForecastResponse>(`/api/stocks/${encodeURIComponent(ticker)}/forecast?period=${period}`, 3600),

  getBacktest: (
    ticker: string,
    params: {
      strategy: BacktestStrategy;
      period?: Period;
      fast?: number;
      slow?: number;
      rsi_window?: number;
      oversold?: number;
      overbought?: number;
      transaction_cost_bps?: number;
      slippage_bps?: number;
    }
  ) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) qs.set(key, String(value));
    });
    return request<BacktestResponse>(`/api/stocks/${encodeURIComponent(ticker)}/backtest?${qs.toString()}`, 300);
  },
};

export const authApi = {
  signup: (email: string, password: string, displayName: string) =>
    request<TokenResponse>("/api/auth/signup", undefined, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, display_name: displayName }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/api/auth/login", undefined, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    }),

  me: (token: string) => request<UserOut>("/api/auth/me", undefined, authHeaders(token)),
};

export const watchlistApi = {
  list: (token: string) => request<WatchlistItemOut[]>("/api/watchlist", undefined, authHeaders(token)),

  add: (token: string, ticker: string) =>
    request<WatchlistItemOut>("/api/watchlist", undefined, authJson(token, { ticker }, "POST")),

  remove: (token: string, ticker: string) =>
    request<void>(`/api/watchlist/${encodeURIComponent(ticker)}`, undefined, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    }),
};

export const portfolioApi = {
  listHoldings: (token: string) => request<HoldingOut[]>("/api/portfolio/holdings", undefined, authHeaders(token)),

  addHolding: (
    token: string,
    holding: { ticker: string; shares: number; cost_basis_per_share: number; purchase_date: string; notes?: string }
  ) => request<HoldingOut>("/api/portfolio/holdings", undefined, authJson(token, holding, "POST")),

  updateHolding: (token: string, id: string, patch: Partial<Omit<HoldingAnalytics, "id">>) =>
    request<HoldingOut>(`/api/portfolio/holdings/${id}`, undefined, authJson(token, patch, "PUT")),

  deleteHolding: (token: string, id: string) =>
    request<void>(`/api/portfolio/holdings/${id}`, undefined, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    }),

  analytics: (token: string) =>
    request<PortfolioAnalyticsResponse>("/api/portfolio/analytics", undefined, authHeaders(token)),
};

export const screenerApi = {
  screen: (criteria: ScreenerCriteria) => {
    const params = new URLSearchParams();
    Object.entries(criteria).forEach(([key, value]) => {
      if (value !== undefined && value !== "") params.set(key, String(value));
    });
    return request<ScreenerResponse>(`/api/screener?${params.toString()}`);
  },
};
