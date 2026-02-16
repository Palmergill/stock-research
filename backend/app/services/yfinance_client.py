"""
Yahoo Finance Client - Earnings Estimates Only

This module provides analyst earnings estimates from Yahoo Finance.
Used as a supplement to Polygon.io (which doesn't provide estimates).
"""

import yfinance as yf
from typing import Optional, Dict, List
import logging
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class YFinanceEstimatesClient:
    """Yahoo Finance client - fetches only earnings estimates."""
    
    def __init__(self):
        self._cache = {}
        self._last_request = 0
        self._min_delay = 3  # Seconds between requests to avoid rate limits
    
    def _rate_limit(self):
        """Enforce minimum delay between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)
        self._last_request = time.time()
    
    def _fetch_with_retry(self, ticker: str, max_retries: int = 3) -> Optional[List[Dict]]:
        """Fetch earnings with exponential backoff on rate limits."""
        for attempt in range(max_retries):
            try:
                self._rate_limit()
                stock = yf.Ticker(ticker)
                
                # Try earnings_dates first (most reliable for estimates)
                try:
                    earnings_dates = stock.earnings_dates
                    if earnings_dates is not None and not earnings_dates.empty:
                        logger.info(f"[Yahoo] Found earnings_dates for {ticker}")
                        earnings_data = []
                        for idx, row in earnings_dates.iterrows():
                            fiscal_date = idx.date() if hasattr(idx, 'date') else None
                            
                            reported = row.get("Reported EPS") if "Reported EPS" in row else None
                            estimated = row.get("EPS Estimate") if "EPS Estimate" in row else None
                            surprise = row.get("Surprise(%)") if "Surprise(%)" in row else None
                            
                            earnings_data.append({
                                "fiscal_date": fiscal_date.isoformat() if fiscal_date else None,
                                "reported_eps": float(reported) if reported is not None and not pd.isna(reported) else None,
                                "estimated_eps": float(estimated) if estimated is not None and not pd.isna(estimated) else None,
                                "surprise_pct": float(surprise) if surprise is not None and not pd.isna(surprise) else None,
                            })
                        return earnings_data
                except Exception as e:
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        wait_time = (attempt + 1) * 5  # 5s, 10s, 15s
                        logger.warning(f"[Yahoo] Rate limit on attempt {attempt + 1}, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    logger.debug(f"[Yahoo] earnings_dates failed: {e}")
                
                # If we get here, either no data or non-rate-limit error
                return None
                
            except Exception as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"[Yahoo] Rate limit on attempt {attempt + 1}, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                logger.error(f"[Yahoo] Error on attempt {attempt + 1}: {e}")
                return None
        
        logger.error(f"[Yahoo] Failed after {max_retries} attempts")
        return None
    
    def get_earnings_estimates(self, ticker: str) -> Optional[List[Dict]]:
        """
        Get earnings estimates and actuals from Yahoo Finance.
        
        Returns list of earnings records with:
        - fiscal_date
        - reported_eps (actual)
        - estimated_eps (analyst consensus)
        - surprise_pct (beat/miss percentage)
        """
        ticker = ticker.upper()
        
        # Check cache (Yahoo data changes slowly - cache for 6 hours)
        cache_key = f"estimates_{ticker}"
        cached = self._cache.get(cache_key)
        if cached:
            age = datetime.utcnow() - cached["timestamp"]
            if age < timedelta(hours=6):
                logger.info(f"[Yahoo] Using cached estimates for {ticker}")
                return cached["data"]
        
        logger.info(f"[Yahoo] Fetching earnings estimates for {ticker}")
        
        # Fetch with retry logic for rate limits
        earnings_data = self._fetch_with_retry(ticker)
        
        if earnings_data:
            # Cache the result
            self._cache[cache_key] = {
                "data": earnings_data,
                "timestamp": datetime.utcnow()
            }
            logger.info(f"[Yahoo] Retrieved {len(earnings_data)} earnings records for {ticker}")
            return earnings_data
        
        logger.warning(f"[Yahoo] No earnings estimates found for {ticker}")
        return None
    
    def merge_with_polygon(self, polygon_earnings: List[Dict], yahoo_estimates: Optional[List[Dict]]) -> List[Dict]:
        """
        Merge Yahoo estimates into Polygon earnings data.
        
        Strategy:
        - Use Polygon for actual reported EPS (more accurate)
        - Use Yahoo for estimated EPS and surprise %
        - Match by fiscal_date when possible
        """
        if not yahoo_estimates:
            return polygon_earnings
        
        # Create lookup by date from Yahoo data
        yahoo_by_date = {}
        for e in yahoo_estimates:
            date_key = e.get("fiscal_date")
            if date_key:
                yahoo_by_date[date_key] = e
        
        # Merge into Polygon data
        merged = []
        for poly in polygon_earnings:
            date_key = poly.get("fiscal_date")
            yahoo = yahoo_by_date.get(date_key) if date_key else None
            
            merged_record = poly.copy()
            
            if yahoo:
                # Add Yahoo estimates if Polygon doesn't have them
                if yahoo.get("estimated_eps") is not None and poly.get("estimated_eps") is None:
                    merged_record["estimated_eps"] = yahoo["estimated_eps"]
                
                # Add surprise % from Yahoo
                if yahoo.get("surprise_pct") is not None:
                    merged_record["surprise_pct"] = yahoo["surprise_pct"]
                
                # If Yahoo has reported EPS but Polygon doesn't, use Yahoo's
                if yahoo.get("reported_eps") is not None and poly.get("reported_eps") is None:
                    merged_record["reported_eps"] = yahoo["reported_eps"]
            
            merged.append(merged_record)
        
        return merged


# Import pandas for type checking
try:
    import pandas as pd
except ImportError:
    pd = None

# Singleton instance
yfinance_estimates_client = YFinanceEstimatesClient()
