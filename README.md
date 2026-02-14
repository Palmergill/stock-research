# Stock Research App

A web app for analyzing stock earnings trends. Search any ticker, view EPS actual vs estimated, earnings surprises, and key metrics.

## Stack

- **Backend:** FastAPI + SQLite + yfinance
- **Frontend:** React + TypeScript + Vite + Recharts
- **Data:** Yahoo Finance (free, via yfinance library)

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Deployment (Railway)

See [DEPLOY.md](DEPLOY.md) for detailed instructions.

Quick start:
```bash
git init && git add . && git commit -m "init"
# Push to GitHub, then connect Railway
```

## Features (MVP)

- ✅ Search by ticker
- ✅ EPS actual vs estimated (bar + line chart)
- ✅ Earnings surprise % (bar chart)
- ✅ Key metrics (market cap, P/E, next earnings)
- ✅ 24-hour data caching

## Roadmap

- [ ] Revenue chart (when data available)
- [ ] Historical price overlay
- [ ] Compare multiple stocks
- [ ] Export to CSV/PDF
- [ ] Watchlist
