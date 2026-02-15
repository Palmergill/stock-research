# Architecture Overview

## System Architecture

```
┌─────────────────┐     HTTPS      ┌──────────────────┐
│   User Browser  │ ──────────────> │  Vercel (Static) │
│                 │ <────────────── │   Frontend       │
└─────────────────┘                 └────────┬─────────┘
                                             │
                                             │ Fetch API
                                             │
                              ┌──────────────▼──────────┐
                              │    Railway (Backend)    │
                              │  ┌───────────────────┐  │
                              │  │   FastAPI App     │  │
                              │  │  - REST API       │  │
                              │  │  - CORS enabled   │  │
                              │  └─────────┬─────────┘  │
                              │            │             │
                              │  ┌─────────▼─────────┐  │
                              │  │   Data Service    │  │
                              │  │ - Polygon.io (1°) │  │
                              │  │ - Yahoo Finance   │  │
                              │  └─────────┬─────────┘  │
                              │            │             │
                              │  ┌─────────▼─────────┐  │
                              │  │   PostgreSQL      │  │
                              │  │  - 1 hour cache   │  │
                              │  │  - Auto-migration │  │
                              │  └───────────────────┘  │
                              └─────────────────────────┘
```

## Request Flow

1. **User opens page** → Vercel serves static HTML/JS/CSS
2. **Auto-load TSLA** → Frontend calls `/api/stocks/TSLA`
3. **Backend checks cache** → Query PostgreSQL for existing data
4. **Cache hit (< 1 hour)** → Return cached data
5. **Cache miss** → Call Polygon.io API
6. **Store in PostgreSQL** → Upsert record
7. **Return to frontend** → Render charts

## Data Sources Priority

1. **Polygon.io** (Primary)
   - Real-time prices
   - Historical financials
   - Quarterly data
   - Company fundamentals
   - Requires API key

2. **Yahoo Finance** (Fallback)
   - Free tier
   - Rate limited
   - Used when Polygon fails

## Calculated Metrics

Some metrics are calculated from raw financial data:

| Metric | Calculation | Source Fields |
|--------|-------------|---------------|
| **P/E Ratio** | Price / TTM EPS | `close` / sum of 4Q `basic_earnings_per_share` |
| **Revenue Growth** | (Current Q - YoY Q) / YoY Q | `revenues` current vs 4 quarters prior |
| **ROE** | Net Income / Equity × 100 | `net_income_loss` / `equity` |
| **Debt-to-Equity** | Total Liabilities / Equity | `liabilities` / `equity` |
| **Free Cash Flow** | Latest quarter FCF | `net_cash_flow_from_operating_activities` |

## Frontend Structure

```
static/
├── index.html          # Main page with tabbed interface
├── style.css           # All styling
├── app.js              # All JavaScript logic
└── vercel.json         # Vercel configuration
```

## Backend Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, routes
│   ├── database.py             # SQLAlchemy models
│   ├── database_migration.py   # Auto-migration logic
│   ├── models.py               # Pydantic schemas
│   ├── routers/
│   │   └── stocks.py           # API endpoints
│   └── services/
│       ├── polygon_client.py   # Polygon.io integration
│       ├── yfinance_client.py  # Main data client
│       ├── stock_data.py       # Search functionality
│       ├── finnhub_client.py   # (unused, kept for fallback)
│       └── alpha_vantage_client.py  # (unused, kept for fallback)
├── requirements.txt
└── Dockerfile
```

## Caching Strategy

- **TTL:** 1 hour
- **Storage:** PostgreSQL
- **Key:** Ticker symbol (unique constraint)
- **Refresh:** Manual via button or `?refresh=true` query param
- **Fallback:** Always fetch fresh if cache miss

## Security Considerations

- CORS limited to `palmergill.com` and localhost
- API keys stored in Railway environment variables
- No user authentication (public app)
- No PII stored

## Performance

- **Cache hit:** ~50ms response
- **Cache miss (Polygon):** ~500-1000ms
- **Cache miss (Yahoo):** ~2000-5000ms
- **Charts:** Client-side Canvas rendering
- **Bundle size:** ~27KB (uncompressed HTML/CSS/JS)
