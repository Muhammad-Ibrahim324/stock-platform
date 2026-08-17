# PRD: Stock Market Research & Analytics Platform

## 1. Product Overview

Build a polished, production-style **Stock Market Research & Analytics Platform** that allows users to search publicly traded companies, analyze historical market data, compare stocks, evaluate technical indicators, inspect financial metrics, simulate portfolios, and experiment with forecasting models.

The goal is to create a project that looks like a serious financial analytics product rather than a basic stock-price prediction notebook.

The application should demonstrate:

- Full-stack development
- Financial data analysis
- Data visualization
- Time-series analysis
- Machine learning
- Portfolio analytics
- API integration
- Clean UI/UX
- Production-quality code structure

This project should be suitable for publishing publicly on GitHub and showcasing on a resume.

---

# 2. Product Goal

A user should be able to search a stock ticker such as:

```text
AAPL
MSFT
NVDA
AMD
GOOGL
TSLA
```

and immediately receive a professional research dashboard containing:

- Current and historical price information
- Returns
- Volume
- Volatility
- Technical indicators
- Financial metrics
- Risk analysis
- Benchmark comparison
- Forecasting experiments
- Portfolio analysis

The product should feel closer to a lightweight research terminal than a beginner stock-prediction app.

---

# 3. Target Users

Primary users:

- Beginner/intermediate investors
- Data analysts
- Finance students
- Quantitative finance learners
- Data science students
- Recruiters reviewing the GitHub project

This application is for **research and educational purposes only**.

Include a visible disclaimer:

> This platform is for educational and research purposes only and does not provide financial or investment advice.

---

# 4. Core User Experience

The main workflow should be:

```text
Search ticker
     ↓
Load company data
     ↓
Display market overview
     ↓
Explore charts and indicators
     ↓
Analyze company fundamentals
     ↓
Measure risk
     ↓
Compare against benchmarks/stocks
     ↓
Run forecasting models
     ↓
Build/test portfolio
```

The application should remain easy to navigate despite containing advanced analytics.

---

# 5. Recommended Technology Stack

Use a modern production-style architecture.

## Frontend

Preferred:

```text
Next.js
TypeScript
Tailwind CSS
Recharts or Plotly
```

Alternative:

```text
React
TypeScript
Tailwind CSS
```

## Backend

Preferred:

```text
Python
FastAPI
Pandas
NumPy
scikit-learn
statsmodels
```

Optional advanced libraries where appropriate:

```text
XGBoost
LightGBM
PyPortfolioOpt
SciPy
```

## Database

Use:

```text
PostgreSQL
```

For development, SQLite may be supported as a fallback.

## Caching

Optional:

```text
Redis
```

Use caching where appropriate to avoid repeatedly requesting identical financial data.

---

# 6. Financial Data

Use a legitimate market-data provider supported by the development environment.

Possible sources include:

- Yahoo Finance-compatible data
- Alpha Vantage
- Financial Modeling Prep
- Polygon
- Twelve Data
- other appropriate financial APIs

Important:

Never expose private API keys in frontend code or GitHub.

Store API credentials using:

```text
.env
```

Include:

```text
.env.example
```

Never commit the actual `.env` file.

Add `.env` to `.gitignore`.

The app should fail gracefully if an API is unavailable or rate-limited.

---

# 7. Main Dashboard

Create a professional dashboard for each stock.

At the top display:

```text
Company Name
Ticker
Exchange
Sector
Industry
Current Price
Daily Change
Daily Change %
Market Cap
52-Week High
52-Week Low
```

Example:

```text
NVIDIA Corporation
NASDAQ: NVDA

$182.43
+3.22 (+1.80%)

Market Cap
$4.4T

52W Range
$86.62 — $190.18
```

Do not overcrowd the header.

Use clear visual hierarchy.

---

# 8. Interactive Price Chart

Create a high-quality interactive stock chart.

Allow users to select:

```text
1D
5D
1M
3M
6M
YTD
1Y
5Y
MAX
```

Display:

- Price
- Volume
- Moving averages

Allow toggling indicators.

Chart interactions should include:

- Hover values
- Zoom if supported
- Crosshair if supported
- Responsive resizing

---

# 9. Technical Analysis

Calculate common technical indicators.

Include:

## Moving averages

```text
SMA 20
SMA 50
SMA 100
SMA 200
EMA 12
EMA 26
```

## Momentum

```text
RSI
MACD
MACD Signal
MACD Histogram
```

## Volatility

```text
Bollinger Bands
ATR
Historical Volatility
```

## Trend

Optional:

```text
ADX
```

Create charts for the indicators.

Do not simply display numbers.

Explain indicators briefly using tooltips or info icons.

---

# 10. Returns Analysis

Analyze historical returns.

Calculate:

```text
Daily Return
Weekly Return
Monthly Return
Annual Return
Cumulative Return
```

Visualizations should include:

### Cumulative returns

Show growth of a hypothetical:

```text
$10,000 investment
```

Example:

```text
Initial Investment
$10,000

Current Value
$18,430

Total Return
+84.3%
```

Also include a daily-return distribution histogram.

---

# 11. Benchmark Comparison

Allow users to compare a stock against benchmarks.

Examples:

```text
S&P 500
NASDAQ-100
Dow Jones
```

Show normalized growth.

Example:

```text
Start all assets at $100
```

Then compare:

```text
NVDA
S&P 500
NASDAQ-100
```

Calculate:

```text
Stock Return
Benchmark Return
Excess Return
Correlation
Beta
```

---

# 12. Risk Analytics

Create a dedicated risk section.

Calculate:

```text
Annualized Volatility
Beta
Sharpe Ratio
Sortino Ratio
Maximum Drawdown
Value at Risk
Conditional Value at Risk
```

Where appropriate, allow risk-free-rate configuration.

Clearly label assumptions.

---

# 13. Drawdown Analysis

Calculate historical drawdowns.

Display:

```text
Maximum Drawdown
Current Drawdown
Longest Drawdown Period
Recovery Time
```

Create a drawdown chart beneath the stock price.

Example:

```text
Maximum Drawdown
-42.8%

Occurred
Nov 2021 – Oct 2022
```

---

# 14. Fundamental Analysis

Create a fundamentals section.

Display available metrics such as:

## Valuation

```text
P/E Ratio
Forward P/E
Price/Sales
Price/Book
PEG Ratio
Enterprise Value
EV/EBITDA
```

## Profitability

```text
Gross Margin
Operating Margin
Net Margin
ROE
ROA
```

## Financial health

```text
Total Cash
Total Debt
Debt/Equity
Current Ratio
Free Cash Flow
```

## Growth

```text
Revenue Growth
Earnings Growth
EPS Growth
```

Handle missing data gracefully.

Never display fake values.

---

# 15. Financial Statements

If the data provider supports them, display:

```text
Income Statement
Balance Sheet
Cash Flow Statement
```

Allow:

```text
Annual
Quarterly
```

Present them in readable financial tables.

Include metrics such as:

```text
Revenue
Gross Profit
Operating Income
Net Income
EPS

Assets
Liabilities
Cash
Debt
Equity

Operating Cash Flow
Capital Expenditures
Free Cash Flow
```

---

# 16. Stock Comparison Tool

Allow users to select approximately:

```text
2–5 stocks
```

Example:

```text
NVDA
AMD
INTC
AVGO
```

Compare them across:

```text
Price performance
Market capitalization
Revenue growth
P/E
Profit margins
Volatility
Sharpe ratio
Maximum drawdown
Beta
```

Include comparison charts and a comparison table.

---

# 17. Correlation Analysis

Allow the user to analyze correlations among multiple assets.

Generate a correlation matrix.

Example:

```text
       AAPL  MSFT  NVDA  AMD
AAPL   1.00  0.71  0.58 0.49
MSFT   0.71  1.00  0.66 0.52
NVDA   0.58  0.66  1.00 0.77
AMD    0.49  0.52  0.77 1.00
```

Display it visually as a heatmap.

---

# 18. Portfolio Builder

Create a portfolio-analysis page.

Users should be able to add stocks and set weights.

Example:

```text
AAPL    25%
MSFT    25%
NVDA    30%
GOOGL   20%
```

Validate:

```text
Total allocation = 100%
```

Calculate:

```text
Portfolio Return
Portfolio Volatility
Sharpe Ratio
Maximum Drawdown
Beta
```

Create:

- Allocation chart
- Historical portfolio-value chart
- Drawdown chart
- Contribution by asset

---

# 19. Portfolio Optimization

Add optional quantitative portfolio optimization.

Support:

```text
Maximum Sharpe Portfolio
Minimum Volatility Portfolio
Equal Weight Portfolio
```

Plot an:

```text
Efficient Frontier
```

Compare optimized portfolios against equal weighting.

Clearly explain that historical optimization does not guarantee future performance.

---

# 20. Monte Carlo Simulation

Create a Monte Carlo portfolio simulation.

Allow configuration of:

```text
Initial Investment
Simulation Horizon
Number of Simulations
```

Example:

```text
Initial investment:
$10,000

Horizon:
1 year

Simulations:
5,000
```

Output:

```text
Median Ending Value

5th Percentile

95th Percentile

Probability of Loss
```

Display simulated portfolio paths.

---

# 21. Forecasting Lab

Create a separate section called:

# Forecasting Lab

Do not present predictions as guaranteed future prices.

The purpose is to demonstrate time-series modeling.

Models can include:

```text
Naive baseline
Moving-average baseline
Linear Regression
ARIMA
Exponential Smoothing
Random Forest
XGBoost
```

Optional advanced model:

```text
LSTM
```

Do not add a deep-learning model simply for appearance.

Only include it if implemented properly.

---

# 22. Forecast Evaluation

This is extremely important.

Do not simply train on all historical data and predict forward.

Use:

```text
Training period
Validation period
Test period
```

Prefer:

```text
Walk-forward validation
```

Evaluate models using:

```text
MAE
RMSE
MAPE
Directional Accuracy
```

Compare every forecasting model against a naive baseline.

Create a table:

| Model         | MAE | RMSE | MAPE | Direction Accuracy |
| ------------- | --: | ---: | ---: | -----------------: |
| Naive         |     |      |      |                    |
| ARIMA         |     |      |      |                    |
| Random Forest |     |      |      |                    |
| XGBoost       |     |      |      |                    |

Clearly identify the best-performing model.

---

# 23. Feature Engineering for ML Forecasting

Potential features:

```text
Lagged returns
SMA
EMA
RSI
MACD
Volume changes
Volatility
Momentum
Rolling returns
Rolling standard deviation
```

Prevent data leakage.

Every feature at time `t` must only use information available at or before time `t`.

---

# 24. Forecast Visualization

Display:

```text
Historical price
Test predictions
Future experimental forecast
Confidence interval where appropriate
```

Use different visual treatment for observed and predicted periods.

Add text stating:

> Forecasts are statistical experiments based on historical data and should not be interpreted as investment recommendations.

---

# 25. Backtesting

Create a strategy-testing section.

Start with simple strategies such as:

## Moving Average Crossover

Example:

```text
Buy:
50-day SMA crosses above 200-day SMA

Exit:
50-day SMA crosses below 200-day SMA
```

## RSI Strategy

Example:

```text
Buy:
RSI < 30

Exit:
RSI > 70
```

Allow users to compare against:

```text
Buy & Hold
```

---

# 26. Backtesting Metrics

Calculate:

```text
Total Return
Annualized Return
Volatility
Sharpe Ratio
Maximum Drawdown
Win Rate
Number of Trades
```

Include transaction-cost assumptions.

Avoid unrealistic results caused by look-ahead bias.

---

# 27. Screener

Optional but strongly recommended.

Build a basic stock screener.

Allow filtering by:

```text
Market Cap
Sector
P/E
Revenue Growth
Dividend Yield
Volatility
RSI
Price Performance
```

Example:

```text
Market Cap > $10B
P/E < 30
Revenue Growth > 10%
RSI < 60
```

Return matching companies in a sortable table.

---

# 28. Watchlist

Allow users to create a watchlist.

Example:

```text
My Watchlist

AAPL
NVDA
MSFT
AMD
GOOGL
```

Display:

```text
Price
Daily %
1M %
YTD %
P/E
Market Cap
```

Persist the watchlist using either:

- Local storage for MVP
- User database if authentication is implemented

---

# 29. Search

Create a global stock search field.

The user should be able to search by:

```text
Ticker
Company name
```

Example:

```text
Search: NVIDIA
```

Result:

```text
NVDA — NVIDIA Corporation
```

Include autocomplete if feasible.

---

# 30. UI / UX Design

# 30. UI / UX Design

The design should look like a real financial analytics platform.

Avoid:

* Excessive gradients
* Random glowing elements
* Giant rounded cards everywhere
* Excessive emojis
* Fake AI-style dashboards
* Unnecessary animations
* Generic template appearance

Use:

* Clean typography
* Strong hierarchy
* Neutral professional palette
* Dense but readable financial information
* Clear tabs
* Thoughtful spacing
* Professional chart styling

Possible inspiration:

```text
Bloomberg-style information density
Koyfin
TradingView
Finviz
Modern institutional analytics dashboards
```

Do not directly copy any existing product.

## 30.1 Professional Design Standard — No “AI-Coded” Appearance

The application must **not look like it was generated by an AI coding tool, assembled from generic templates, or created with default components without thoughtful design work**.

The final product should look like it was designed, built, reviewed, and refined by an experienced **professional UI/UX designer and frontend engineer**.

This is a core product requirement, not an optional visual improvement.

### Avoid Common Signs of AI-Generated Interfaces

Do not use:

* Excessive rounded cards
* Random gradients
* Neon glows without purpose
* Too many floating panels
* Repetitive card-after-card layouts
* Oversized headings simply to fill space
* Generic dashboard templates
* Excessive icons
* Decorative icons that provide no usability benefit
* Unnecessary animations
* Excessive glassmorphism
* Every piece of information being placed inside its own card
* Fake statistics or decorative financial data
* Generic AI-generated marketing copy
* Arbitrary visual effects
* Inconsistent spacing
* Inconsistent border radiuses
* Excessive empty space in information-dense areas
* Components that look copied directly from a UI library
* Generic Tailwind/shadcn-style layouts without meaningful customization
* Identical layouts repeated across every page

Do not make the interface visually complicated simply to make it appear advanced.

### Design the Product Intentionally

Use professional product-design principles throughout the application:

* Strong visual hierarchy
* Consistent spacing system
* Purposeful typography
* Carefully controlled information density
* Logical grid structure
* Precise alignment
* Clear grouping of related information
* Subtle borders and separators
* Thoughtful whitespace
* Consistent interaction patterns
* Professional financial tables
* Well-designed charts
* Appropriate chart labeling
* Clear navigation
* Useful empty states
* Meaningful loading states
* Clear hover and active states
* High readability
* Accessible contrast
* Subtle, purposeful motion
* Responsive layouts designed intentionally for each screen size

Every design decision should have a reason.

### Do Not Rely on Default Component Libraries

Tailwind CSS, shadcn/ui, Material UI, Chakra, Radix, or similar tools may be used where appropriate, but their default appearance should **not define the visual identity of the application**.

Customize:

* Typography
* Spacing
* Borders
* Tables
* Navigation
* Inputs
* Buttons
* Tabs
* Charts
* Dropdowns
* Tooltips
* Dialogs
* Loading states
* Data panels

The application should have its own cohesive visual system.

### Financial Product Design

Because this is a financial research platform, prioritize clarity and information density over decorative visuals.

The interface should feel appropriate for someone researching markets for an extended period.

Important information should be immediately identifiable.

For example, stock research screens should make it easy to distinguish:

```text
Current price

Daily change

Historical performance

Valuation

Profitability

Risk

Technical indicators

Forecast results
```

Do not make users search through decorative cards to find important information.

### Inspiration

Study the design quality and information hierarchy of products such as:

```text
TradingView
Koyfin
Bloomberg
Finviz
Stripe Dashboard
Linear
Professional institutional analytics platforms
```

Use these only as references for:

* Information hierarchy
* Typography
* Navigation
* Data presentation
* Interaction quality
* Layout discipline
* Chart usability

Do **not** directly copy their branding, layouts, visual assets, or proprietary design.

### Charts Must Look Professionally Designed

Charts are one of the most important visual elements in this application.

Avoid default chart-library appearances.

Charts should have:

* Appropriate axis formatting
* Clear legends
* Proper financial number formatting
* Useful hover tooltips
* Consistent typography
* Logical time ranges
* Proper spacing
* Responsive sizing
* Clear comparison between datasets
* Subtle gridlines where useful
* Accessible visual differentiation
* No unnecessary decorative effects

Every chart should answer a meaningful analytical question.

### Tables Must Feel Like Financial Software

Financial tables should support scanning large amounts of information quickly.

Use:

* Proper number alignment
* Consistent decimal formatting
* Percentage formatting
* Currency formatting
* Clear column hierarchy
* Useful sorting
* Sticky headers where appropriate
* Subtle row separation
* Responsive behavior
* Clear positive/negative value treatment

Do not turn every table row into a separate card.

### Motion and Animation

Animation should be restrained.

Use animation only when it improves:

* Navigation
* State changes
* Loading feedback
* Chart transitions
* User orientation

Avoid:

* Constant floating animations
* Pulsing gradients
* Excessive entrance animations
* Dramatic page transitions
* Decorative 3D effects
* Animations that delay access to information

Professional financial software should feel **fast and precise**.

### Responsive Design Must Be Intentional

Do not create the desktop interface and simply stack everything vertically on mobile.

Review each major page independently at:

```text
Large desktop
Laptop
Tablet
Mobile
```

Determine which information should:

* Remain visible
* Collapse
* Move into tabs
* Become horizontally scrollable
* Be simplified
* Be hidden when genuinely unnecessary

The mobile version should feel deliberately designed.

### Final Professional UI Review

Before declaring any page complete, review it using the following questions:

1. Does anything look like a default template?
2. Does anything immediately suggest AI-generated UI?
3. Are there unnecessary cards?
4. Are components repeated without a design reason?
5. Is spacing consistent?
6. Is alignment precise?
7. Is the typography hierarchy obvious?
8. Can important financial information be found quickly?
9. Are charts professionally formatted?
10. Are financial tables easy to scan?
11. Does every visual element serve a purpose?
12. Are interaction patterns consistent?
13. Is the interface cohesive across all pages?
14. Does the product have its own visual identity?
15. Does the mobile interface feel intentionally designed?
16. Are there unnecessary animations or effects?
17. Would this interface look credible if released as a real commercial product?
18. Would an experienced designer consider the page finished rather than merely functional?

If the answer to any of these reveals that an area feels:

```text
Generic
Template-like
AI-generated
Unfinished
Inconsistent
Overly decorative
Poorly aligned
Visually repetitive
```

refine that area before considering the feature complete.

### Required Final Standard

The finished application should look like a **professionally designed, production-ready financial analytics platform**, not a coding demonstration.

A recruiter, developer, investor, or user opening the product should reasonably believe that substantial professional UI/UX work went into designing it.

The application should feel:

**intentional, cohesive, precise, polished, fast, credible, and production-ready.**

Functionality alone is not sufficient.

The visual execution and user experience should receive the same level of attention as the financial calculations, backend architecture, and machine-learning implementation.




---

# 31. Main Navigation

Suggested navigation:

```text
Overview

Markets

Research

Compare

Portfolio

Forecasting Lab

Backtesting

Screener

Watchlist
```

Keep navigation simple.

---

# 32. Responsive Design

Support:

```text
Desktop
Laptop
Tablet
Mobile
```

Desktop should provide the richest experience.

On mobile:

- Stack charts vertically
- Collapse complex tables
- Maintain readable financial metrics
- Keep navigation accessible

---

# 33. Loading States

Financial APIs may take time.

Create proper loading states.

Use:

- Skeleton cards
- Chart skeletons
- Table skeletons

Do not show blank screens.

---

# 34. Error Handling

Handle:

```text
Invalid ticker
API failure
Missing financial data
Rate limiting
Network error
Insufficient historical data
```

Give meaningful messages.

Example:

```text
No historical data could be found for this ticker.
```

Do not crash the application.

---

# 35. Backend API Architecture

Create clean API routes.

Example:

```text
GET /api/stocks/{ticker}/overview

GET /api/stocks/{ticker}/prices

GET /api/stocks/{ticker}/technicals

GET /api/stocks/{ticker}/fundamentals

GET /api/stocks/{ticker}/risk

POST /api/compare

POST /api/portfolio/analyze

POST /api/portfolio/optimize

POST /api/forecast

POST /api/backtest
```

Use proper request/response schemas.

---

# 36. Code Architecture

Do not create one giant file.

Use modular organization.

Example:

```text
project/
│
├── frontend/
│   ├── components/
│   ├── pages/
│   ├── hooks/
│   ├── services/
│   ├── types/
│   └── utils/
│
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   ├── analytics/
│   ├── forecasting/
│   ├── portfolio/
│   ├── backtesting/
│   └── tests/
│
├── notebooks/
│
├── docs/
│
├── screenshots/
│
├── .env.example
├── .gitignore
├── docker-compose.yml
├── README.md
└── LICENSE
```

---

# 37. Jupyter Notebooks

Include a `/notebooks` folder for research and model experimentation.

Suggested notebooks:

```text
01_market_data_exploration.ipynb

02_returns_and_risk.ipynb

03_technical_indicators.ipynb

04_forecasting_experiments.ipynb

05_portfolio_optimization.ipynb

06_backtesting.ipynb
```

The final application logic should not depend on running notebooks.

Move reusable production logic into Python modules.

---

# 38. Testing

Include automated tests.

Test:

```text
API endpoints
Return calculations
Technical indicators
Risk metrics
Portfolio weights
Forecast preprocessing
Backtesting logic
```

Pay particular attention to:

```text
Look-ahead bias
Data leakage
Incorrect dates
Missing values
Division by zero
```

---

# 39. Security

Do not expose:

```text
API keys
Database passwords
Secrets
Tokens
```

Use environment variables.

Validate user inputs.

Sanitize ticker queries.

Apply API rate limiting where necessary.

---

# 40. Performance

Cache financial data.

Do not download years of identical market data every time the page reloads.

Potential caching rules:

```text
Historical daily data:
cache longer

Intraday/current values:
cache briefly

Fundamental data:
cache longer
```

---

# 41. Docker Support

Include:

```text
Dockerfile
docker-compose.yml
```

A developer should ideally be able to run:

```bash
docker compose up
```

and launch the application locally.

---

# 42. README Requirements

The GitHub README is a major part of this project.

Create a professional README containing:

## Project title

## Short description

## Screenshots

## Live demo

## Features

## Architecture

## Tech stack

## Installation

## Environment variables

## Usage

## API architecture

## Machine-learning methodology

## Forecast validation methodology

## Backtesting methodology

## Results

## Limitations

## Financial disclaimer

## Future improvements

## License

---

# 43. Architecture Diagram

Include an architecture diagram.

Example:

```text
                 ┌──────────────────┐
                 │ Financial APIs   │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ Data Service     │
                 │ + Cache          │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │ FastAPI Backend  │
                 └───────┬──────────┘
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
Analytics Engine   Forecast Engine   Portfolio Engine
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                 ┌──────────────────┐
                 │ Next.js Frontend │
                 └──────────────────┘
```

Create a visually polished version for the README.

---

# 44. Documentation

Important calculations should be documented.

Examples:

```text
Annualized volatility

Sharpe ratio

Maximum drawdown

Beta

Value at Risk

Portfolio variance

Monte Carlo simulation
```

Explain assumptions.

---

# 45. Demo Experience

When someone opens the application for the first time, automatically provide a default example ticker.

Example:

```text
AAPL
```

This ensures the dashboard does not initially appear empty.

---

# 46. GitHub Quality Requirements

The repository must look professional.

Include:

```text
Descriptive commit history
Clean folder organization
Useful comments
Type hints
Docstrings
Testing
Screenshots
Architecture diagrams
Environment example
License
Setup instructions
```

Remove:

```text
Unused code
Console logs
Temporary scripts
Test API keys
Large unnecessary data files
Generated build folders
```

---

# 47. Resume-Level Outcome

The finished project should be strong enough to support a resume bullet similar to:

> Built a full-stack quantitative market research platform using Python, FastAPI, React/Next.js and financial APIs, incorporating technical analysis, risk modeling, portfolio optimization, Monte Carlo simulation, walk-forward time-series forecasting, and strategy backtesting.

Another possible bullet:

> Developed an end-to-end financial analytics system supporting multi-asset comparison, portfolio optimization, risk metrics, interactive visualization, forecasting model evaluation, and historical strategy backtesting.

The actual README should provide enough evidence to substantiate these claims.

---

# 48. Important Modeling Rules

Follow these strictly.

### Do not claim that stock prices can reliably be predicted.

Treat forecasting as a statistical experiment.

### Never use future data during model training.

Prevent data leakage.

### Always include a baseline model.

Advanced models must outperform the baseline before being presented as improvements.

### Separate training and test data chronologically.

Never randomly shuffle time-series data.

### Document assumptions.

### Do not fabricate unavailable financial information.

### Never call the application an investment advisor.

---

# 49. MVP Build Priority

Build in this order.

## Phase 1 — Core

1. Project architecture
2. Market-data integration
3. Stock search
4. Stock overview
5. Historical price charts
6. Technical indicators
7. Returns analysis
8. Risk metrics

## Phase 2 — Research

9. Fundamentals
10. Stock comparison
11. Benchmark comparison
12. Correlation analysis
13. Financial statements

## Phase 3 — Quantitative Tools

14. Portfolio builder
15. Portfolio optimization
16. Efficient frontier
17. Monte Carlo simulation

## Phase 4 — Data Science

18. Forecasting lab
19. Baseline model
20. Time-series validation
21. ML forecasting
22. Model comparison

## Phase 5 — Advanced

23. Backtesting
24. Screener
25. Watchlist
26. Authentication if necessary
27. Deployment
28. Documentation

---

# 50. Final Acceptance Criteria

The project is complete when:

- Users can search valid stock tickers.
- Historical market data loads correctly.
- Interactive charts work.
- Technical indicators are calculated correctly.
- Returns and risk metrics are displayed.
- Stocks can be compared.
- Benchmarks can be compared.
- Portfolio analytics work.
- Portfolio optimization works.
- Monte Carlo simulation works.
- Forecasting uses chronological validation.
- Models are evaluated against a baseline.
- Backtests avoid look-ahead bias.
- Missing data is handled safely.
- API keys are protected.
- The application is responsive.
- The backend is modular.
- Automated tests exist.
- Docker setup works.
- The repository contains a professional README.
- Screenshots and architecture documentation are included.
- The project can be publicly uploaded to GitHub without exposing secrets.

---

# 51. Final Instruction to Coding Agent

Build this as a **real portfolio-quality financial analytics application**, not as a prototype filled with placeholder components.

Prioritize:

1. Correct financial calculations
2. Clean architecture
3. Reliable data handling
4. Professional UI/UX
5. Meaningful analytics
6. Honest ML evaluation
7. Strong documentation
8. GitHub readiness

Do not add features solely for visual complexity.

Do not fabricate financial data.

Do not expose API keys.

Do not use placeholder charts once real data integration is available.

Before declaring the project complete:

- Run the frontend build
- Run backend tests
- Check API calls
- Test multiple tickers
- Test invalid tickers
- Test missing data
- Test mobile responsiveness
- Verify `.gitignore`
- Verify no secrets are present
- Verify the README installation instructions
- Verify the application can be cloned and run by another developer
