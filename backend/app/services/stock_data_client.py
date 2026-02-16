"""
Stock Data Client - Polygon.io Exclusive

This module provides unified access to stock data from Polygon.io.
No fallback data sources - Polygon is the single source of truth.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.database import EarningsRecord, StockSummary
from app.services.polygon_client import polygon_client
import logging

logger = logging.getLogger(__name__)

# Cache TTLs optimized for data type
CACHE_TTL = {
    "price": timedelta(minutes=1),        # Prices change frequently
    "financials": timedelta(hours=24),    # Financials change quarterly
    "company_info": timedelta(hours=24),  # Company info rarely changes
}


class StockDataClient:
    """
    Primary stock data client - Polygon.io exclusive.
    
    Design principles:
    - Single source of truth: Polygon.io
    - Smart caching: Different TTL per data type
    - Graceful degradation: Serve stale cache if API fails
    - Clear errors: Specific messages for different failure modes
    """
    
    def __init__(self):
        if not polygon_client.is_configured():
            logger.warning("Polygon API key not configured. Client will not function.")
    
    def _is_cache_fresh(self, fetched_at: datetime, data_type: str = "price") -> bool:
        """
        Check if cached data is still fresh based on data type.
        
        Args:
            fetched_at: When the data was fetched
            data_type: Type of data (affects TTL) - price, financials, company_info
        """
        ttl = CACHE_TTL.get(data_type, timedelta(hours=1))
        return datetime.utcnow() - fetched_at < ttl
    
    def get_stock_data(self, ticker: str, db: Session, force_refresh: bool = False) -> dict:
        """
        Get comprehensive stock data for a ticker.
        
        Args:
            ticker: Stock symbol (e.g., "TSLA")
            db: Database session
            force_refresh: If True, bypass cache and fetch fresh data
        
        Returns:
            dict with ticker, name, summary, and earnings
        
        Raises:
            Exception: If Polygon API fails and no cache available
        """
        ticker = ticker.upper().strip()
        
        # Validate API is configured
        if not polygon_client.is_configured():
            # Try to serve from cache even if API is down
            cached = self._get_cached_data(ticker, db, accept_stale=True)
            if cached:
                cached["_warning"] = "Using cached data - API key not configured"
                return cached
            raise Exception("Polygon API key not configured and no cached data available")
        
        # Check cache unless force_refresh
        if not force_refresh:
            cached = self._get_cached_data(ticker, db)
            if cached:
                logger.info(f"[{ticker}] Serving from cache")
                return cached
        
        # Fetch fresh data from Polygon
        try:
            logger.info(f"[{ticker}] Fetching from Polygon.io")
            data = polygon_client.get_stock_data(ticker)
            return self._save_polygon_data(ticker, data, db)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{ticker}] Polygon API error: {error_msg}")
            
            # Try to serve stale cache as fallback
            stale_data = self._get_cached_data(ticker, db, accept_stale=True)
            if stale_data:
                hours_old = self._get_cache_age_hours(stale_data.get("_fetched_at"))
                stale_data["_warning"] = f"Using {hours_old} hour old data - API temporarily unavailable"
                logger.warning(f"[{ticker}] Serving stale cache ({hours_old}h old)")
                return stale_data
            
            # No cache available - raise specific error
            if "429" in error_msg or "rate limit" in error_msg.lower():
                raise Exception(f"Rate limit exceeded for {ticker}. Please try again in a minute.")
            elif "404" in error_msg or "not found" in error_msg.lower():
                raise Exception(f"Ticker '{ticker}' not found. Please check the symbol.")
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                raise Exception("API authentication failed. Please check your Polygon API key.")
            else:
                raise Exception(f"Could not fetch data for {ticker}: {error_msg}")
    
    def _get_cached_data(self, ticker: str, db: Session, accept_stale: bool = False) -> Optional[dict]:
        """
        Retrieve cached data from database.
        
        Args:
            ticker: Stock symbol
            db: Database session
            accept_stale: If True, return data even if cache is expired
        """
        summary = db.query(StockSummary).filter(StockSummary.ticker == ticker).first()
        if not summary:
            return None
        
        # Check if cache is fresh (or if we accept stale)
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
        """Calculate how old the cache is in hours."""
        if not fetched_at_iso:
            return 0
        try:
            fetched_at = datetime.fromisoformat(fetched_at_iso.replace('Z', '+00:00'))
            age = datetime.utcnow() - fetched_at.replace(tzinfo=None)
            return round(age.total_seconds() / 3600, 1)
        except:
            return 0
    
    def _save_polygon_data(self, ticker: str, data: dict, db: Session) -> dict:
        """
        Save Polygon.io data to database.
        
        Args:
            ticker: Stock symbol
            data: Raw data from Polygon API
            db: Database session
        """
        logger.info(f"[{ticker}] Saving data to database")
        
        # Delete old earnings records
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
                price=current_price  # Use actual price, not random
            )
            db.add(record)
        
        # Upsert summary with all metrics
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
        
        # Return formatted response
        summary = db.query(StockSummary).filter(StockSummary.ticker == ticker).first()
        earnings = db.query(EarningsRecord).filter(
            EarningsRecord.ticker == ticker
        ).order_by(EarningsRecord.fiscal_date.desc()).all()
        
        return self._format_response(ticker, summary, earnings)
    
    def _format_response(self, ticker: str, summary: StockSummary, earnings: List[EarningsRecord]) -> dict:
        """
        Format database records into API response.
        
        Args:
            ticker: Stock symbol
            summary: StockSummary record
            earnings: List of EarningsRecord records
        """
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


# Singleton instance for backwards compatibility
yfinance_client = StockDataClient()
