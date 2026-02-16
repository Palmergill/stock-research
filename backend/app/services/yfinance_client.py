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
        self._min_delay = 2  # Seconds between requests to avoid rate limits
    
    def _rate_limit(self):
        """Enforce minimum delay between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)
        self._last_request = time.time()
    
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
        
        try:
            logger.info(f"[Yahoo] Fetching earnings estimates for {ticker}")
            
            # Rate limit to avoid 429 errors
            self._rate_limit()
            
            stock = yf.Ticker(ticker)
            
            # Try to get earnings calendar/history with estimates
            # yfinance has different methods depending on version
            earnings_data = []
            
            # Method 1: Try quarterly_earnings (has estimates in newer versions)
            try:
                q_earnings = stock.quarterly_earnings
                if q_earnings is not None and not q_earnings.empty:
                    logger.info(f"[Yahoo] Found quarterly_earnings for {ticker}")
                    for idx, row in q_earnings.iterrows():
                        # Parse date from index
                        fiscal_date = None
                        if isinstance(idx, str):
                            try:
                                from datetime import datetime
                                fiscal_date = datetime.strptime(idx, "%Y-%m-%d").date()
                            except:
                                pass
                        
                        earnings_data.append({
                            "fiscal_date": fiscal_date.isoformat() if fiscal_date else None,
                            "reported_eps": float(row.get("Reported EPS")) if pd.notna(row.get("Reported EPS")) else None,
                            "estimated_eps": float(row.get("Surprise(%)")) if pd.notna(row.get("Surprise(%)")) else None,  # May be surprise%
                        })
            except Exception as e:
                logger.debug(f"[Yahoo] quarterly_earnings failed: {e}")
            
            # Method 2: Try calendar for upcoming estimates
            try:
                calendar = stock.calendar
                if calendar is not None and not calendar.empty:
                    logger.info(f"[Yahoo] Found calendar for {ticker}")
                    # Calendar usually has next earnings date and estimates
                    for idx, row in calendar.iterrows():
                        if "Earnings" in str(idx) or "EPS" in str(idx):
                            earnings_data.append({
                                "fiscal_date": None,  # Upcoming
                                "estimated_eps": float(row.get("Value")) if pd.notna(row.get("Value")) else None,
                            })
            except Exception as e:
                logger.debug(f"[Yahoo] calendar failed: {e}")
            
            # Method 3: Try earnings_dates (newer yfinance versions)
            try:
                earnings_dates = stock.earnings_dates
                if earnings_dates is not None and not earnings_dates.empty:
                    logger.info(f"[Yahoo] Found earnings_dates for {ticker}")
                    for idx, row in earnings_dates.iterrows():
                        fiscal_date = idx.date() if hasattr(idx, 'date') else None
                        
                        # These columns vary by yfinance version
                        reported = row.get("Reported EPS") if "Reported EPS" in row else None
                        estimated = row.get("EPS Estimate") if "EPS Estimate" in row else None
                        surprise = row.get("Surprise(%)") if "Surprise(%)" in row else None
                        
                        earnings_data.append({
                            "fiscal_date": fiscal_date.isoformat() if fiscal_date else None,
                            "reported_eps": float(reported) if reported is not None and not pd.isna(reported) else None,
                            "estimated_eps": float(estimated) if estimated is not None and not pd.isna(estimated) else None,
                            "surprise_pct": float(surprise) if surprise is not None and not pd.isna(surprise) else None,
                        })
            except Exception as e:
                logger.debug(f"[Yahoo] earnings_dates failed: {e}")
            
            if earnings_data:
                logger.info(f"[Yahoo] Retrieved {len(earnings_data)} earnings records for {ticker}")
                # Cache the result
                self._cache[cache_key] = {
                    "data": earnings_data,
                    "timestamp": datetime.utcnow()
                }
                return earnings_data
            
            logger.warning(f"[Yahoo] No earnings estimates found for {ticker}")
            return None
            
        except Exception as e:
            logger.error(f"[Yahoo] Error fetching estimates for {ticker}: {e}")
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
