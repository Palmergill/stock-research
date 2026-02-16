"""
Stock Data Client - Polygon.io Primary + Yahoo Finance Estimates

This module provides unified access to stock data.
- Polygon.io: Primary source for financials, prices, company info
- Yahoo Finance: Supplement for analyst earnings estimates only
"""

from datetime import datetime, timedelta
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

# Cache TTLs optimized for data type
CACHE_TTL = {
    "price": timedelta(minutes=1),
    "financials": timedelta(hours=24),
    "company_info": timedelta(hours=24),
}


class StockDataClient:
    """Primary stock data client - Polygon.io primary, Yahoo for estimates."""
    
    def __init__(self):
        self._polygon_client = None
        self._yfinance_client = None
    
    @property
    def polygon(self):
        """Lazy import of polygon client to avoid circular imports."""
        if self._polygon_client is None:
            from app.services.polygon_client import polygon_client
            self._polygon_client = polygon_client
        return self._polygon_client
    
    @property
    def yahoo(self):
        """Lazy import of Yahoo Finance client for estimates."""
        if self._yfinance_client is None:
            from app.services.yfinance_client import yfinance_estimates_client
            self._yfinance_client = yfinance_estimates_client
        return self._yfinance_client
    
    def _is_cache_fresh(self, fetched_at: datetime, data_type: str = "price") -> bool:
        """Check if cached data is still fresh based on data type."""
        ttl = CACHE_TTL.get(data_type, timedelta(hours=1))
        return datetime.utcnow() - fetched_at < ttl
    
    def get_stock_data(self, ticker: str, db, force_refresh: bool = False) -> dict:
        """Get comprehensive stock data for a ticker."""
        from app.database import EarningsRecord, StockSummary
        
        ticker = ticker.upper().strip()
        
        # Validate API is configured
        if not self.polygon.is_configured():
            cached = self._get_cached_data(ticker, db, accept_stale=True)
            if cached:
                cached["_warning"] = "Using cached data - API key not configured"
                return cached
            raise Exception("Polygon API key not configured")
        
        # Check cache unless force_refresh
        if not force_refresh:
            cached = self._get_cached_data(ticker, db)
            if cached:
                logger.info(f"[{ticker}] Serving from cache")
                return cached
        
        # Fetch fresh data from Polygon
        try:
            logger.info(f"[{ticker}] Fetching from Polygon.io")
            data = self.polygon.get_stock_data(ticker)
            
            # Fetch Yahoo earnings estimates and merge
            try:
                logger.info(f"[{ticker}] Fetching earnings estimates from Yahoo Finance")
                yahoo_estimates = self.yahoo.get_earnings_estimates(ticker)
                if yahoo_estimates:
                    data["earnings"] = self.yahoo.merge_with_polygon(
                        data.get("earnings", []), 
                        yahoo_estimates
                    )
                    logger.info(f"[{ticker}] Merged Yahoo estimates into earnings data")
            except Exception as e:
                logger.warning(f"[{ticker}] Could not fetch Yahoo estimates: {e}")
                # Continue without estimates - not critical
            
            return self._save_polygon_data(ticker, data, db)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{ticker}] Polygon API error: {error_msg}")
            
            # Try to serve stale cache
            stale_data = self._get_cached_data(ticker, db, accept_stale=True)
            if stale_data:
                hours_old = self._get_cache_age_hours(stale_data.get("_fetched_at"))
                stale_data["_warning"] = f"Using {hours_old}h old data - API error"
                return stale_data
            
            # Raise specific error
            if "429" in error_msg or "rate limit" in error_msg.lower():
                raise Exception(f"Rate limit exceeded. Try again in a minute.")
            elif "404" in error_msg or "not found" in error_msg.lower():
                raise Exception(f"Ticker '{ticker}' not found.")
            elif "401" in error_msg:
                raise Exception("API authentication failed. Check your Polygon API key.")
            else:
                raise Exception(f"Could not fetch data: {error_msg}")
    
    def _get_cached_data(self, ticker: str, db, accept_stale: bool = False):
        """Retrieve cached data from database."""
        from app.database import EarningsRecord, StockSummary
        
        summary = db.query(StockSummary).filter(StockSummary.ticker == ticker).first()
        if not summary:
            return None
        
        cache_age = datetime.utcnow() - summary.fetched_at
        max_ttl = max(CACHE_TTL.values())
        
        if not accept_stale and cache_age > max_ttl:
            return None
        
        earnings = db.query(EarningsRecord).filter(
            EarningsRecord.ticker == ticker
        ).order_by(EarningsRecord.fiscal_date.desc()).all()
        
        result = self._format_response(ticker, summary, earnings)
        result["_fetched_at"] = summary.fetched_at.isoformat()
        result["_cache_age_hours"] = round(cache_age.total_seconds() / 3600, 1)
        
        return result
    
    def _get_cache_age_hours(self, fetched_at_iso: Optional[str]) -> float:
        """Calculate cache age in hours."""
        if not fetched_at_iso:
            return 0
        try:
            fetched_at = datetime.fromisoformat(fetched_at_iso.replace('Z', '+00:00'))
            age = datetime.utcnow() - fetched_at.replace(tzinfo=None)
            return round(age.total_seconds() / 3600, 1)
        except:
            return 0
    
    def _save_polygon_data(self, ticker: str, data: dict, db) -> dict:
        """Save Polygon.io data to database."""
        from app.database import EarningsRecord, StockSummary
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        
        logger.info(f"[{ticker}] Saving data to database")
        
        # Delete old earnings
        db.query(EarningsRecord).filter(EarningsRecord.ticker == ticker).delete(
            synchronize_session=False
        )
        
        # Add new earnings records
        current_price = data.get("current_price") or 0
        for e in data.get("earnings", []):
            record = EarningsRecord(
                ticker=ticker,
                fiscal_date=e.get("fiscal_date") or datetime.utcnow().date(),
                period=e.get("period", "Q"),
                reported_eps=e.get("reported_eps"),
                estimated_eps=e.get("estimated_eps"),
                surprise_pct=e.get("surprise_pct"),
                revenue=e.get("revenue"),
                free_cash_flow=e.get("free_cash_flow"),
                pe_ratio=data.get("pe_ratio"),
                price=current_price
            )
            db.add(record)
        
        # Upsert summary
        summary_values = {
            "ticker": ticker,
            "name": data.get("name", ticker),
            "market_cap": data.get("market_cap"),
            "current_price": data.get("current_price"),
            "pe_ratio": data.get("pe_ratio"),
            "revenue_growth": data.get("revenue_growth"),
            "free_cash_flow": data.get("free_cash_flow"),
            "profit_margin": data.get("profit_margin"),
            "operating_margin": data.get("operating_margin"),
            "roe": data.get("roe"),
            "debt_to_equity": data.get("debt_to_equity"),
            "dividend_yield": data.get("dividend_yield"),
            "beta": data.get("beta"),
            "price_52w_high": data.get("price_52w_high"),
            "price_52w_low": data.get("price_52w_low"),
            "next_earnings_date": data.get("next_earnings_date"),
            "fetched_at": datetime.utcnow()
        }
        
        stmt = pg_insert(StockSummary).values(**summary_values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker"],
            set_=summary_values
        )
        db.execute(stmt)
        db.commit()
        
        summary = db.query(StockSummary).filter(StockSummary.ticker == ticker).first()
        earnings = db.query(EarningsRecord).filter(
            EarningsRecord.ticker == ticker
        ).order_by(EarningsRecord.fiscal_date.desc()).all()
        
        return self._format_response(ticker, summary, earnings)
    
    def _format_response(self, ticker: str, summary, earnings: List) -> dict:
        """Format database records into API response."""
        return {
            "ticker": ticker,
            "name": summary.name,
            "summary": {
                "ticker": ticker,
                "name": summary.name,
                "market_cap": summary.market_cap,
                "current_price": summary.current_price,
                "pe_ratio": summary.pe_ratio,
                "revenue_growth": summary.revenue_growth,
                "free_cash_flow": summary.free_cash_flow,
                "profit_margin": summary.profit_margin,
                "operating_margin": summary.operating_margin,
                "roe": summary.roe,
                "debt_to_equity": summary.debt_to_equity,
                "dividend_yield": summary.dividend_yield,
                "beta": summary.beta,
                "price_52w_high": summary.price_52w_high,
                "price_52w_low": summary.price_52w_low,
                "next_earnings_date": summary.next_earnings_date.isoformat() if summary.next_earnings_date else None,
            },
            "earnings": [
                {
                    "fiscal_date": e.fiscal_date.isoformat(),
                    "period": e.period,
                    "reported_eps": e.reported_eps,
                    "estimated_eps": e.estimated_eps,
                    "surprise_pct": e.surprise_pct,
                    "revenue": e.revenue,
                    "free_cash_flow": e.free_cash_flow,
                    "pe_ratio": e.pe_ratio,
                    "price": e.price
                }
                for e in sorted(earnings, key=lambda x: x.fiscal_date, reverse=True)
            ],
            "source": "Polygon.io",
            "cached_at": summary.fetched_at.isoformat() if summary.fetched_at else None
        }


# Singleton instance
stock_data_client = StockDataClient()
yfinance_client = stock_data_client  # Backwards compatibility
