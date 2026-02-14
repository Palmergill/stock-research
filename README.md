# Stock Research App

A web app for analyzing stock earnings trends. Search any ticker, view EPS actual vs estimated, earnings surprises, and key metrics.

## Stack

- **Backend:** FastAPI + PostgreSQL/SQLite + yfinance
- **Frontend:** Vanilla HTML/CSS/JS
- **Data:** Yahoo Finance (via yfinance library)
- **Hosting:** Railway (backend) + Vercel (frontend)

## Setup PostgreSQL (Production)

### 1. Create PostgreSQL Database in Railway

1. Go to https://railway.app
2. Click your stock-research project
3. Click **"New"** → **"Database"** → **"Add PostgreSQL"**
4. Railway will create the database and give you a connection URL

### 2. Connect Database to Your Service

1. In your Railway project, click on your **stock-research service**
2. Go to **"Variables"** tab
3. Click **"New Variable"**
4. Add: `DATABASE_URL` with the value from the PostgreSQL database
   - Railway usually auto-injects this as `${{Postgres.DATABASE_URL}}`
5. Remove or update `USE_MOCK_DATA` if you had it set

### 3. Deploy

Railway will auto-deploy when you push to GitHub, or click "Redeploy" manually.

**Benefits of PostgreSQL:**
- ✅ No volume management needed
- ✅ Automatic schema migrations (no data deletion)
- ✅ Better performance
- ✅ Production-grade database

## Local Development

Uses SQLite by default (no setup needed):

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Deployment

Both Railway and Vercel auto-deploy on git push:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

**Railway:** Auto-detects and deploys backend
**Vercel:** Auto-detects and deploys frontend

## Features

- Real-time stock data from Yahoo Finance
- Key metrics: P/E, margins, ROE, debt, beta
- Charts: Price, EPS, Revenue, FCF, P/E
- Tabbed interface: Overview, Earnings, Financials, Valuation
- Autocomplete search by ticker or company name
- 24-hour data caching

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL or SQLite connection string | `sqlite:///./stock_data.db` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) | `http://localhost:5173` |

## Troubleshooting

**Price seems wrong/old:**
- Data is cached for 24 hours
- Clear cache by restarting Railway service
- Or wait for cache to expire

**Charts not loading:**
- Check browser console for errors
- Ensure backend is responding at Railway URL

**Database migration issues:**
- With PostgreSQL: migrations run automatically
- With SQLite: may need to delete volume if migration fails
