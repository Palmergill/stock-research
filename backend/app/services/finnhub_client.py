"""
Finnhub Client - Earnings Estimates

This module provides analyst earnings estimates from Finnhub.
Used as a supplement to Polygon.io (which doesn't provide estimates).
Free tier: 60 calls/minute
"""

import requests
from typing import Optional, Dict, List
import logging
import os
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FinnhubEstimatesClient:
    """Finnhub client - fetches earnings estimates and surprises."""
    
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self):
        self.api_key = os.getenv("FINNHUB_API_KEY")
        self._cache = {}
    
    def is_configured(self) -> bool:
        return self.api_key is not None and self.api_key != ""
    
    def get_earnings_estimates(self, ticker: str) -> Optional[List[Dict]]:
        """
        Get earnings estimates from Finnhub.
        
        Returns list of earnings records with:
        - fiscal_date
        - reported_eps (actual)
        - estimated_eps (analyst consensus)
        - surprise_pct (beat/miss percentage)
        """
        if not self.is_configured():
            logger.debug("[Finnhub] API key not configured")
            return None
        
        ticker = ticker.upper()
        
        # Check cache (6 hours)
        cache_key = f"finnhub_estimates_{ticker}"
        cached = self._cache.get(cache_key)
        if cached:
            age = datetime.utcnow() - cached["timestamp"]
            if age < timedelta(hours=6):
                logger.info(f"[Finnhub] Using cached estimates for {ticker}")
                return cached["data"]
        
        try:
            logger.info(f"[Finnhub] Fetching earnings estimates for {ticker}")
            
            # Get company earnings with estimates
            url = f"{self.BASE_URL}/stock/earnings"
            params = {
                "symbol": ticker,
                "token": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 429:
                logger.warning(f"[Finnhub] Rate limit hit for {ticker}")
                return None
            
            if response.status_code == 403:
                logger.warning("[Finnhub] Invalid API key")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            if not data or not isinstance(data, list):
                logger.warning(f"[Finnhub] No earnings data for {ticker}")
                return None
            
            earnings_data = []
            for item in data:
                # Parse date
                period = item.get("period", "")
                try:
                    # Period format is usually "2024-01" or "2024-Q1"
                    if "-Q" in period:
                        # Quarterly: "2024-Q1" -> approximate date
                        year, q = period.split("-Q")
                        quarter_months = {"1": "03-31", "2": "06-30", "3": "09-30", "4": "12-31"}
                        fiscal_date = f"{year}-{quarter_months.get(q, '12-31')}"
                    else:
                        # Try to parse as date
                        fiscal_date = period
                except:
                    fiscal_date = None
                
                earnings_data.append({
                    "fiscal_date": fiscal_date,
                    "reported_eps": item.get("actual"),
                    "estimated_eps": item.get("estimate"),
                    "surprise_pct": item.get("surprisePercent"),
                    "period": period
                })
            
            if earnings_data:
                logger.info(f"[Finnhub] Retrieved {len(earnings_data)} earnings records for {ticker}")
                # Cache the result
                self._cache[cache_key] = {
                    "data": earnings_data,
                    "timestamp": datetime.utcnow()
                }
                return earnings_data
            
            return None
            
        except Exception as e:
            logger.error(f"[Finnhub] Error fetching estimates for {ticker}: {e}")
            return None
    
    def merge_with_polygon(self, polygon_earnings: List[Dict], finnhub_estimates: Optional[List[Dict]]) -> List[Dict]:
        """
        Merge Finnhub estimates into Polygon earnings data.
        
        Strategy:
        - Use Polygon for actual reported EPS (more accurate)
        - Use Finnhub for estimated EPS and surprise %
        - Match by fiscal_date when possible
        """
        if not finnhub_estimates:
            return polygon_earnings
        
        # Create lookup by date from Finnhub data
        finnhub_by_date = {}
        for e in finnhub_estimates:
            date_key = e.get("fiscal_date")
            if date_key:
                finnhub_by_date[date_key] = e
        
        # Merge into Polygon data
        merged = []
        for poly in polygon_earnings:
            date_key = poly.get("fiscal_date")
            finnhub = finnhub_by_date.get(date_key) if date_key else None
            
            merged_record = poly.copy()
            
            if finnhub:
                # Add Finnhub estimates if Polygon doesn't have them
                if finnhub.get("estimated_eps") is not None and poly.get("estimated_eps") is None:
                    merged_record["estimated_eps"] = finnhub["estimated_eps"]
                
                # Add surprise % from Finnhub
                if finnhub.get("surprise_pct") is not None:
                    merged_record["surprise_pct"] = finnhub["surprise_pct"]
            
            merged.append(merged_record)
        
        return merged


# Singleton instance
finnhub_estimates_client = FinnhubEstimatesClient()
