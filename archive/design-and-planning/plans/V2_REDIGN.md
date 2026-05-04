# Stock Research App v2.0 Redesign

## Goals

1. **Pure Polygon Architecture** - Remove Yahoo Finance fallback, use Polygon exclusively
2. **Real-time Data** - WebSocket for live price updates
3. **Rich Features** - News, market status, dividends, insider activity
4. **Optimized Caching** - Different TTLs for different data types
5. **Better UX** - Loading states, error handling, progressive enhancement

## New Architecture

### Backend (FastAPI)

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  REST API    │  │  WebSocket   │  │  Background Jobs │  │
│  │  - /stocks   │  │  - /ws       │  │  - News fetcher  │  │
│  │  - /news     │  │  - Real-time │  │  - Market status │  │
│  │  - /market   │  │    prices    │  │  - Dividend sync │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                    │            │
│  ┌──────▼─────────────────▼────────────────────▼─────────┐  │
│  │              Polygon.io Client                        │  │
│  │  - REST API (financials, aggregates, details)       │  │
│  │  - WebSocket (trades, quotes)                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│  ┌─────────────────────────▼────────────────────────────┐  │
│  │              PostgreSQL Cache                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │  │
│  │  │ StockSummary │  │ PriceUpdates │  │ News     │  │  │
│  │  │ (1 hour)     │  │ (real-time)  │  │ (15 min) │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │  │
│  │  │ Financials   │  │ MarketStatus │  │ Dividends│  │  │
│  │  │ (24 hours)   │  │ (1 minute)   │  │ (24 hrs) │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Frontend (Vanilla JS)

```
┌─────────────────────────────────────────────────────────────┐
│                     Single Page App                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Header                                               │  │
│  │  - Search bar (autocomplete)                         │  │
│  │  - Market status indicator                           │  │
│  │  - Real-time clock                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Stock Dashboard                                     │  │
│  │  ┌──────────────┐  ┌──────────────────────────────┐  │  │
│  │  │ Price Card   │  │ Key Metrics Grid             │  │  │
│  │  │ - Live price │  │ - P/E, Growth, FCF, ROE, D/E │  │  │
│  │  │ - Change %   │  │ - Real-time updates          │  │  │
│  │  │ - Chart      │  └──────────────────────────────┘  │  │
│  │  └──────────────┘                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ Tab: Overview│  │ Tab: News    │  │ Tab: Financials  │ │
│  │ - Metrics    │  │ - Latest     │  │ - Statements     │ │
│  │ - Charts     │  │ - Sentiment  │  │ - Ratios         │ │
│  │ - Peers      │  └──────────────┘  └──────────────────┘ │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

## New Endpoints to Implement

### 1. WebSocket - Real-time Prices
```python
@app.websocket("/ws/prices/{ticker}")
async def price_websocket(websocket: WebSocket, ticker: str):
    # Connect to Polygon WebSocket
    # Stream trades to frontend
    # Cache last price in Redis/memory
```

### 2. News Feed
```python
@router.get("/{ticker}/news")
async def get_stock_news(ticker: str, limit: int = 10):
    # GET /v2/reference/news
    # Cache for 15 minutes
    # Return with sentiment analysis
```

### 3. Market Status
```python
@router.get("/market/status")
async def get_market_status():
    # GET /v1/marketstatus/now
    # Cache for 1 minute
    # Return: open/closed, next open, next close
```

### 4. Dividend History
```python
@router.get("/{ticker}/dividends")
async def get_dividends(ticker: str):
    # GET /v3/reference/dividends
    # Cache for 24 hours
    # Return: history, yield, next ex-date
```

### 5. Insider Transactions
```python
@router.get("/{ticker}/insiders")
async def get_insider_transactions(ticker: str):
    # GET /vX/insiders-transactions
    # Cache for 1 hour
    # Return: buys, sells, net activity
```

### 6. Analyst Ratings
```python
@router.get("/{ticker}/analysts")
async def get_analyst_ratings(ticker: str):
    # GET /vX/reference/analyst-ratings
    # Cache for 24 hours
    # Return: buy/hold/sell counts, price targets
```

## Optimized Caching Strategy

| Data Type | Source | TTL | Reason |
|-----------|--------|-----|--------|
| **Stock Price** | WebSocket | Real-time | Changes every second |
| **Price (REST)** | /v2/aggs | 1 minute | Fallback to WebSocket |
| **Financials** | /vX/financials | 24 hours | Only change quarterly |
| **Company Info** | /v3/reference | 24 hours | Rarely changes |
| **News** | /v2/news | 15 minutes | Frequent updates |
| **Market Status** | /v1/status | 1 minute | Opening/closing times |
| **Dividends** | /v3/dividends | 24 hours | Quarterly announcements |
| **Insider** | /vX/insiders | 1 hour | Daily filings |
| **Analyst** | /vX/analysts | 24 hours | Weekly updates |

## Data Models

### New Models

```python
class PriceUpdate(BaseModel):
    ticker: str
    price: float
    change: float
    change_percent: float
    volume: int
    timestamp: datetime
    source: str = "websocket"  # websocket or rest

class NewsArticle(BaseModel):
    id: str
    ticker: str
    title: str
    author: str
    published_utc: datetime
    article_url: str
    image_url: Optional[str]
    summary: Optional[str]
    keywords: List[str]
    sentiment: Optional[str]  # positive, negative, neutral
    fetched_at: datetime

class MarketStatus(BaseModel):
    market: str  # "open", "closed", "extended_hours"
    is_open: bool
    next_open: Optional[datetime]
    next_close: Optional[datetime]
    server_time: datetime

class Dividend(BaseModel):
    ticker: str
    ex_date: date
    record_date: date
    pay_date: date
    cash_amount: float
    dividend_type: str  # CD, SC, LT, ST
    frequency: int  # 0=one-time, 1=annual, 2=bi-annual, 4=quarterly, 12=monthly

class InsiderTransaction(BaseModel):
    ticker: str
    filing_date: datetime
    transaction_date: date
    insider_name: str
    insider_title: str
    transaction_type: str  # P=Purchase, S=Sale
    shares: int
    price: float
    value: float

class AnalystRating(BaseModel):
    ticker: str
    analyst: str
    rating: str  # buy, hold, sell
    price_target: Optional[float]
    date: date
```

## Frontend Changes

### 1. Real-time Price Component
```javascript
class PriceStream {
    constructor(ticker) {
        this.ws = new WebSocket(`wss://api.palmergill.com/ws/prices/${ticker}`);
        this.onPriceUpdate = null;
    }
    
    connect() {
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (this.onPriceUpdate) {
                this.onPriceUpdate(data);
            }
        };
    }
}
```

### 2. Market Status Indicator
```html
<div id="marketStatus" class="market-indicator">
    <span class="status-dot" id="statusDot"></span>
    <span id="statusText">Market Open</span>
    <span id="countdown">Closes in 2h 15m</span>
</div>
```

### 3. News Feed Panel
```html
<div id="newsPanel" class="news-feed">
    <h3>Latest News</h3>
    <div id="newsList">
        <!-- News items loaded dynamically -->
    </div>
</div>
```

### 4. Loading States
```javascript
// Progressive loading
async function loadStockData(ticker) {
    // 1. Show skeleton immediately
    showSkeleton();
    
    // 2. Load cached data first (fast)
    const cached = await loadCached(ticker);
    if (cached) displayResults(cached);
    
    // 3. Fetch fresh data
    const fresh = await fetchFresh(ticker);
    displayResults(fresh);
    
    // 4. Connect WebSocket for real-time
    connectPriceStream(ticker);
}
```

## Implementation Phases

### Phase 1: Core Refactor (Week 1)
- [ ] Remove Yahoo Finance code
- [ ] Implement optimized caching
- [ ] Add proper error handling for Polygon-only
- [ ] Update database schema for new models

### Phase 2: Real-time (Week 2)
- [ ] Implement WebSocket server
- [ ] Connect to Polygon WebSocket
- [ ] Frontend price streaming
- [ ] Add market status indicator

### Phase 3: News & Data (Week 3)
- [ ] News endpoint and frontend panel
- [ ] Dividend history
- [ ] Enhanced metrics display
- [ ] Sentiment analysis

### Phase 4: Advanced (Week 4)
- [ ] Insider transactions
- [ ] Analyst ratings
- [ ] Peer comparison
- [ ] Market overview page

## Error Handling Strategy

Since we're going Polygon-only:

1. **Rate Limit (429)**
   - Exponential backoff
   - Queue requests
   - Show "Rate limit reached, retrying..."

2. **API Down**
   - Serve stale cache if available
   - Show "Using cached data from X hours ago"
   - Auto-retry every 30 seconds

3. **Invalid Ticker**
   - Clear error message
   - Suggest similar tickers

4. **Partial Data**
   - Show what's available
   - Gray out unavailable metrics
   - Explain why (e.g., "Financials not yet filed")

## Database Schema Changes

### New Tables

```sql
-- Price updates (time-series, could use TimescaleDB)
CREATE TABLE price_updates (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price FLOAT NOT NULL,
    change FLOAT,
    change_percent FLOAT,
    volume BIGINT,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    source VARCHAR(20) DEFAULT 'websocket'
);

CREATE INDEX idx_price_updates_ticker_time ON price_updates(ticker, timestamp DESC);

-- News articles
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    article_id VARCHAR(100) UNIQUE NOT NULL,
    ticker VARCHAR(10) NOT NULL,
    title TEXT NOT NULL,
    author VARCHAR(255),
    published_at TIMESTAMP NOT NULL,
    article_url TEXT NOT NULL,
    image_url TEXT,
    summary TEXT,
    keywords TEXT[],
    sentiment VARCHAR(20),
    fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_news_ticker ON news_articles(ticker, published_at DESC);

-- Market status (single row, updated frequently)
CREATE TABLE market_status (
    id SERIAL PRIMARY KEY,
    market VARCHAR(50) DEFAULT 'us',
    is_open BOOLEAN NOT NULL,
    next_open TIMESTAMP,
    next_close TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Dividends
CREATE TABLE dividends (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    ex_date DATE NOT NULL,
    record_date DATE,
    pay_date DATE,
    cash_amount FLOAT NOT NULL,
    dividend_type VARCHAR(10),
    frequency INTEGER,
    fetched_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(ticker, ex_date)
);

-- Insider transactions
CREATE TABLE insider_transactions (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    filing_date TIMESTAMP NOT NULL,
    transaction_date DATE NOT NULL,
    insider_name VARCHAR(255),
    insider_title VARCHAR(255),
    transaction_type VARCHAR(5),
    shares INTEGER,
    price FLOAT,
    value FLOAT,
    fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_insider_ticker ON insider_transactions(ticker, transaction_date DESC);

-- Analyst ratings
CREATE TABLE analyst_ratings (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    analyst VARCHAR(255),
    rating VARCHAR(20),
    price_target FLOAT,
    rating_date DATE,
    fetched_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ratings_ticker ON analyst_ratings(ticker, rating_date DESC);
```

## Benefits of This Redesign

1. **Simpler Architecture** - No fallback logic, single source of truth
2. **Real-time Experience** - Live price updates via WebSocket
3. **Richer Data** - News, insider, analyst data adds depth
4. **Better Performance** - Optimized caching per data type
5. **Professional Quality** - Market status, sentiment, etc.
6. **Scalable** - WebSocket handles many concurrent users

## Potential Challenges

1. **Rate Limits** - Need careful management without fallback
2. **API Costs** - More endpoints = more calls
3. **Complexity** - WebSocket adds operational complexity
4. **Cache Invalidation** - Different TTLs need careful management

## Next Steps

Ready to implement? I can start with:
1. **Phase 1** - Core refactor (remove Yahoo, optimize caching)
2. **Database migrations** - Add new tables
3. **WebSocket setup** - Real-time price streaming
4. **Frontend redesign** - New UI components

Which phase should we start with?
