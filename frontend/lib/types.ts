// Mirrors backend/app/api/schemas.py. Keep these in sync when the API changes.

export type DataSource =
  | "yfinance"
  | "alpha_vantage"
  | "financial_modeling_prep"
  | "synthetic_demo";

export type Period = "1d" | "5d" | "1mo" | "3mo" | "6mo" | "ytd" | "1y" | "2y" | "5y" | "10y" | "max";

export interface OverviewResponse {
  ticker: string;
  company_name: string;
  exchange: string | null;
  sector: string | null;
  industry: string | null;
  currency: string;
  price: number;
  previous_close: number;
  change: number;
  change_percent: number;
  market_cap: number | null;
  week52_high: number | null;
  week52_low: number | null;
  dividend_yield: number | null;
  source: DataSource;
  is_synthetic: boolean;
}

export interface OHLCVBar {
  trade_date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  adj_close: number;
  volume: number;
}

export interface PriceHistoryResponse {
  ticker: string;
  period: string;
  bars: OHLCVBar[];
  source: DataSource;
  is_synthetic: boolean;
}

export interface IndicatorPoint {
  trade_date: string;
  sma_20: number | null;
  sma_50: number | null;
  sma_100: number | null;
  sma_200: number | null;
  ema_12: number | null;
  ema_26: number | null;
  rsi_14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
  atr_14: number | null;
  historical_volatility_21d: number | null;
  adx_14: number | null;
}

export interface TechnicalsResponse {
  ticker: string;
  period: string;
  points: IndicatorPoint[];
  source: DataSource;
  is_synthetic: boolean;
}

export interface GrowthPoint {
  trade_date: string;
  value: number;
}

export interface ReturnsDistribution {
  bin_edges: number[];
  counts: number[];
  mean_pct: number;
  std_pct: number;
}

export interface ReturnsResponse {
  ticker: string;
  period: string;
  total_return_pct: number;
  annualized_return_pct: number;
  initial_investment: number;
  ending_value: number;
  growth_series: GrowthPoint[];
  distribution: ReturnsDistribution;
  source: DataSource;
  is_synthetic: boolean;
}

export interface DrawdownPoint {
  trade_date: string;
  drawdown_pct: number;
}

export interface RiskResponse {
  ticker: string;
  period: string;
  benchmark: string | null;
  annualized_volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  max_drawdown_peak_date: string | null;
  max_drawdown_trough_date: string | null;
  max_drawdown_recovery_date: string | null;
  max_drawdown_recovery_days: number | null;
  current_drawdown_pct: number;
  value_at_risk_95: number;
  conditional_value_at_risk_95: number;
  risk_free_rate_assumed: number;
  beta: number | null;
  correlation_to_benchmark: number | null;
  drawdown_series: DrawdownPoint[];
  source: DataSource;
  is_synthetic: boolean;
}

export interface FundamentalsResponse {
  ticker: string;
  pe_ratio: number | null;
  forward_pe: number | null;
  price_to_sales: number | null;
  price_to_book: number | null;
  peg_ratio: number | null;
  ev_to_ebitda: number | null;
  gross_margin: number | null;
  operating_margin: number | null;
  net_margin: number | null;
  return_on_equity: number | null;
  return_on_assets: number | null;
  total_cash: number | null;
  total_debt: number | null;
  debt_to_equity: number | null;
  current_ratio: number | null;
  free_cash_flow: number | null;
  revenue_growth: number | null;
  earnings_growth: number | null;
  source: DataSource;
  is_synthetic: boolean;
}

export interface SearchResult {
  ticker: string;
  name: string;
  exchange: string | null;
}

export type StatementType = "income_statement" | "balance_sheet" | "cash_flow";
export type StatementFrequency = "annual" | "quarterly";

export interface StatementLineItem {
  label: string;
  values: Record<string, number | null>;
}

export interface FinancialStatementResponse {
  ticker: string;
  statement_type: StatementType;
  frequency: StatementFrequency;
  periods: string[];
  line_items: StatementLineItem[];
  source: DataSource;
  is_synthetic: boolean;
}

export interface DividendPayment {
  ex_date: string;
  amount: number;
}

export interface DividendsResponse {
  ticker: string;
  payments: DividendPayment[];
  trailing_annual_dividend_rate: number | null;
  dividend_yield: number | null;
  source: DataSource;
  is_synthetic: boolean;
}

export interface CompareSeries {
  ticker: string;
  normalized_return_pct: { trade_date: string; value: number }[];
  total_return_pct: number;
  annualized_volatility: number;
  source: DataSource;
  is_synthetic: boolean;
}

export interface CompareExcluded {
  ticker: string;
  reason: string;
}

export interface CompareResponse {
  period: string;
  tickers: string[];
  series: CompareSeries[];
  correlation_matrix: Record<string, Record<string, number>>;
  excluded: CompareExcluded[];
}

export interface ApiErrorBody {
  detail: string;
}

// --- Forecasting & Backtesting ---
export interface ForecastPoint {
  trade_date: string;
  actual_pct: number;
  predicted_pct: number;
}

export interface ForecastResponse {
  ticker: string;
  period: string;
  n_predictions: number;
  min_train_days: number;
  refit_interval_days: number;
  model_mae_pct: number | null;
  model_rmse_pct: number | null;
  naive_zero_mae_pct: number | null;
  naive_zero_rmse_pct: number | null;
  model_directional_accuracy_pct: number | null;
  naive_persistence_directional_accuracy_pct: number | null;
  beats_naive_mae: boolean | null;
  beats_naive_directional: boolean | null;
  next_predicted_return_pct: number | null;
  chart_series: ForecastPoint[];
  source: DataSource;
  is_synthetic: boolean;
  disclaimer: string;
}

export type BacktestStrategy = "sma_crossover" | "rsi_mean_reversion" | "buy_and_hold";

export interface EquityPoint {
  trade_date: string;
  strategy_value: number;
  buy_hold_value: number;
}

export interface BacktestMetrics {
  total_return_pct: number;
  annualized_return_pct: number;
  annualized_volatility_pct: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
}

export interface BacktestResponse {
  ticker: string;
  period: string;
  strategy: BacktestStrategy;
  params: Record<string, number>;
  transaction_cost_bps: number;
  slippage_bps: number;
  num_trades: number;
  total_costs_pct: number;
  strategy_metrics: BacktestMetrics;
  buy_hold_metrics: BacktestMetrics;
  outperformance_pct: number;
  equity_curve: EquityPoint[];
  source: DataSource;
  is_synthetic: boolean;
  disclaimer: string;
}

// --- Auth ---
export interface UserOut {
  id: string;
  email: string;
  display_name: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserOut;
}

// --- Watchlist ---
export interface WatchlistItemOut {
  ticker: string;
  added_at: string;
  price: number | null;
  change: number | null;
  change_percent: number | null;
  source: DataSource | null;
  is_synthetic: boolean;
}

// --- Portfolio ---
export interface HoldingOut {
  id: string;
  ticker: string;
  shares: number;
  cost_basis_per_share: number;
  purchase_date: string;
  notes: string | null;
  created_at: string;
}

export interface HoldingAnalytics {
  id: string;
  ticker: string;
  shares: number;
  cost_basis_per_share: number;
  cost_basis_total: number;
  current_price: number | null;
  current_value: number | null;
  gain_loss: number | null;
  gain_loss_pct: number | null;
  weight_pct: number | null;
  source: DataSource | null;
  is_synthetic: boolean;
}

export interface PortfolioRiskSummary {
  annualized_volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown_pct: number;
  beta: number | null;
  correlation_to_benchmark: number | null;
}

export interface PortfolioAnalyticsResponse {
  holdings: HoldingAnalytics[];
  total_cost_basis: number;
  total_current_value: number;
  total_gain_loss: number;
  total_gain_loss_pct: number;
  allocation_by_ticker: Record<string, number>;
  allocation_by_sector: Record<string, number>;
  risk: PortfolioRiskSummary | null;
  risk_note: string;
  excluded: { ticker: string; reason: string }[];
  is_synthetic: boolean;
}

// --- Screener ---
export interface ScreenerResult {
  ticker: string;
  company_name: string;
  sector: string | null;
  price: number | null;
  change_percent: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  dividend_yield: number | null;
  is_synthetic: boolean;
}

export interface ScreenerResponse {
  results: ScreenerResult[];
  candidates_scanned: number;
  candidates_available: number;
  is_synthetic: boolean;
  note: string;
}

export interface ScreenerCriteria {
  sector?: string;
  min_market_cap?: number;
  max_market_cap?: number;
  min_price?: number;
  max_price?: number;
  min_pe?: number;
  max_pe?: number;
  min_dividend_yield?: number;
  candidate_limit?: number;
}
