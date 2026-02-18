# Stock Research App v2.0.0

A professional stock analysis web app with real-time data, interactive charts, and comprehensive financial metrics.

**Live:** https://palmergill.com

## What's New in v2.0.0

- **54 Frontend Polish Tasks** — Complete UI/UX overhaul with animations, mobile support, accessibility
- **Chart.js Integration** — Professional charts with smooth animations and hover tooltips
- **54 Frontend Polish Tasks** — Complete UI/UX overhaul with animations, mobile support, accessibility
- **Mobile-First Design** — Pull-to-refresh, bottom sheets, swipe gestures
- **Dark Theme** — Professional fintech aesthetic with gradient accents
- **Full Accessibility** — prefers-reduced-motion, high contrast mode, keyboard navigation

## What's New in v1.0.2

- **5 Key Metrics Overview** — P/E Ratio, Revenue Growth (YoY), Free Cash Flow, Debt-to-Equity, ROE
- **Calculated Financial Metrics** — ROE and Debt-to-Equity computed from balance sheet data
- **Revenue Growth Tracking** — Year-over-year comparison using quarterly financials
- **Improved P/E Calculation** — TTM EPS from reported earnings per share
- **Better Error Handling** — Defensive API response validation

## Architecture

### Backend
- **Framework:** FastAPI (Python)
- **Database:** PostgreSQL (production) / SQLite (development)
- **Primary Data Source:** Polygon.io (professional-grade stock data)
- **Fallback:** Yahoo Finance (via yfinance)
- **Cache:** 1-hour TTL with manual refresh
- **Hosting:** Railway

### Frontend
- **Stack:** Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Charts:** Chart.js (professional line charts with animations)
- **Hosting:** Vercel
- **Features:** Tabbed interface, autocomplete search, responsive design, 54 polish improvements

## Data Flow

```
User Search → Polygon.io API → PostgreSQL Cache → Frontend Charts
                ↓ (fallback)
          Yahoo Finance
```

1. **Primary:** Polygon.io provides real-time prices, financials, and historical data
2. **Fallback:** Yahoo Finance if Polygon fails or rate-limited
3. **Cache:** PostgreSQL stores data for 1 hour to reduce API calls
4. **Refresh:** Manual refresh button bypasses cache for instant updates

## Features

### Current v1.0.2
- ✅ **5 Key Metrics Overview** — P/E Ratio, Revenue Growth (YoY), Free Cash Flow, Debt-to-Equity, ROE
- ✅ **Real-time stock data** from Polygon.io with Yahoo Finance fallback
- ✅ **Interactive charts:** Price, EPS, Revenue, Free Cash Flow, P/E Ratio
- ✅ **Detailed metrics:** Market Cap, Margins, Beta, 52-week range
- ✅ **Tabbed interface:** Overview, Earnings, Financials, Valuation
- ✅ **Autocomplete search** by ticker or company name
- ✅ **Manual refresh** button for instant data updates
- ✅ **1-hour cache** with PostgreSQL persistence
- ✅ **Mobile-responsive** design

### Upcoming
- [ ] User authentication & watchlists
- [ ] Export data to CSV/PDF
- [ ] Compare multiple stocks
- [ ] Price alerts

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `POLYGON_API_KEY` | **Yes** | Your Polygon.io API key |
| `DATABASE_URL` | Auto | PostgreSQL connection string (auto-injected by Railway) |
| `ALLOWED_ORIGINS` | No | CORS origins (default: includes palmergill.com) |

### Getting Polygon.io API Key

1. Sign up at https://polygon.io
2. Choose a plan (Starter plan is $49/month, or use free tier for limited requests)
3. Copy your API key
4. Add to Railway: Dashboard → Your Project → Variables → `POLYGON_API_KEY`

## Local Development

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Without Polygon (uses Yahoo only)
uvicorn app.main:app --reload

# With Polygon
POLYGON_API_KEY=your_key_here uvicorn app.main:app --reload
```

### Frontend
```bash
cd static
# Serve with any static file server
python -m http.server 8080
# Or use VS Code Live Server extension
```

## Deployment

Both Railway and Vercel auto-deploy on git push:

```bash
git add .
git commit -m "[v1.0.1] Your description"
git push origin main
```

### Version Convention
- Update `VERSION` file
- Update version in `static/index.html`
- Prefix commits: `[v1.0.2] Description`

## Database Schema

### StockSummary
| Column | Type | Description |
|--------|------|-------------|
| ticker | VARCHAR(PK) | Stock symbol |
| name | VARCHAR | Company name |
| market_cap | FLOAT | Market capitalization |
| current_price | FLOAT | Current stock price |
| pe_ratio | FLOAT | Price-to-earnings ratio |
| revenue_growth | FLOAT | YoY revenue growth % |
| free_cash_flow | FLOAT | Latest quarter FCF |
| profit_margin | FLOAT | Net profit margin % |
| operating_margin | FLOAT | Operating margin % |
| roe | FLOAT | Return on equity % |
| debt_to_equity | FLOAT | Debt-to-equity ratio |
| dividend_yield | FLOAT | Dividend yield % |
| beta | FLOAT | Stock beta |
| price_52w_high | FLOAT | 52-week high |
| price_52w_low | FLOAT | 52-week low |
| fetched_at | TIMESTAMP | Cache timestamp |

### EarningsRecord
| Column | Type | Description |
|--------|------|-------------|
| ticker | VARCHAR | Stock symbol |
| fiscal_date | DATE | Quarter end date |
| period | VARCHAR | Q1, Q2, Q3, Q4 |
| reported_eps | FLOAT | Actual EPS |
| estimated_eps | FLOAT | Estimated EPS |
| surprise_pct | FLOAT | % surprise |
| revenue | FLOAT | Quarterly revenue |
| free_cash_flow | FLOAT | Free cash flow |
| pe_ratio | FLOAT | P/E at time |
| price | FLOAT | Stock price |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stocks/search?q={query}` | Search stocks by name/ticker |
| GET | `/api/stocks/{ticker}` | Get stock data (cached) |
| GET | `/api/stocks/{ticker}?refresh=true` | Force refresh |
| GET | `/health` | Health check |

## Troubleshooting

### "Could not fetch data" errors
- Check `POLYGON_API_KEY` is set in Railway
- Check Polygon.io dashboard for rate limits
- Click **↻ Refresh** to retry with Yahoo fallback

### Stale data
- Data is cached for 1 hour
- Use **↻ Refresh** button for instant updates
- Or add `?refresh=true` to API call

### Database errors
- Tables are auto-created on startup
- If issues persist, check Railway PostgreSQL logs

## Tech Stack Summary

| Component | Technology |
|-----------|------------|
| Backend API | FastAPI |
| Database | PostgreSQL (SQLAlchemy ORM) |
| Data Sources | Polygon.io (primary), Yahoo Finance (fallback) |
| Frontend | Vanilla JS, Canvas API |
| Styling | CSS3 with CSS variables |
| Hosting | Railway (backend), Vercel (frontend) |
| Version | v1.0.2 |

## License

MIT - Built with 🦞 by Larry
