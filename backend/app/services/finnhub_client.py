import requests
from typing import Optional, Dict
import os
import logging

logger = logging.getLogger(__name__)

class FinnhubClient:
    """Finnhub API client (free tier: 60 calls/minute)"""
    
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self):
        self.api_key = os.getenv("FINNHUB_API_KEY")
    
    def is_configured(self) -> bool:
        return self.api_key is not None
    
    def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Fetch stock data from Finnhub"""
        if not self.api_key:
            return None
        
        try:
            # Get company profile
            profile_response = requests.get(
                f"{self.BASE_URL}/stock/profile2",
                params={"symbol": ticker, "token": self.api_key},
                timeout=10
            )
            profile_response.raise_for_status()
            profile = profile_response.json()
            
            if not profile or not profile.get("name"):
                logger.warning(f"No Finnhub profile for {ticker}")
                return None
            
            # Get quote (current price)
            quote_response = requests.get(
                f"{self.BASE_URL}/quote",
                params={"symbol": ticker, "token": self.api_key},
                timeout=10
            )
            quote_response.raise_for_status()
            quote = quote_response.json()
            
            # Get basic financials
            metrics_response = requests.get(
                f"{self.BASE_URL}/stock/metric",
                params={"symbol": ticker, "metric": "all", "token": self.api_key},
                timeout=10
            )
            metrics_response.raise_for_status()
            metrics_data = metrics_response.json()
            metrics = metrics_data.get("metric", {})
            
            return {
                "name": profile.get("name", ticker),
                "market_cap": self._parse_float(profile.get("marketCapitalization")) * 1e6 if profile.get("marketCapitalization") else None,
                "pe_ratio": self._parse_float(metrics.get("peBasicExclExtraTTM")),
                "profit_margin": self._parse_float(metrics.get("netProfitMarginTTM")),
                "operating_margin": self._parse_float(metrics.get("operatingMarginTTM")),
                "roe": self._parse_float(metrics.get("roeTTM")),
                "debt_to_equity": self._parse_float(metrics.get("totalDebt/totalEquityQuarterly")),
                "dividend_yield": self._parse_float(metrics.get("dividendYieldIndicatedAnnual")),
                "beta": self._parse_float(metrics.get("beta")),
                "price_52w_high": self._parse_float(metrics.get("52WeekHigh")),
                "price_52w_low": self._parse_float(metrics.get("52WeekLow")),
                "current_price": self._parse_float(quote.get("c")),  # Current price
                "next_earnings_date": None,  # Not available in free tier
            }
            
        except Exception as e:
            logger.warning(f"Finnhub error for {ticker}: {e}")
            return None
    
    def _parse_float(self, value) -> Optional[float]:
        if value is None or value == "None" or value == "":
            return None
        try:
            return float(value)
        except:
            return None

# Singleton instance
finnhub_client = FinnhubClient()
