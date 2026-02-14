import requests
from typing import Optional, Dict
import os
import logging

logger = logging.getLogger(__name__)

class AlphaVantageClient:
    """Alpha Vantage API client (free tier: 5 calls/min, 500/day)"""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self):
        self.api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    
    def is_configured(self) -> bool:
        return self.api_key is not None
    
    def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Fetch stock overview data from Alpha Vantage"""
        if not self.api_key:
            return None
        
        try:
            # Company overview endpoint
            response = requests.get(
                self.BASE_URL,
                params={
                    "function": "OVERVIEW",
                    "symbol": ticker,
                    "apikey": self.api_key
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            if not data or "Symbol" not in data:
                logger.warning(f"No Alpha Vantage data for {ticker}")
                return None
            
            # Get current price from global quote
            quote_response = requests.get(
                self.BASE_URL,
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": ticker,
                    "apikey": self.api_key
                },
                timeout=10
            )
            quote_response.raise_for_status()
            quote_data = quote_response.json()
            
            quote = quote_data.get("Global Quote", {})
            
            return {
                "name": data.get("Name", ticker),
                "market_cap": self._parse_float(data.get("MarketCapitalization")),
                "pe_ratio": self._parse_float(data.get("PERatio")),
                "profit_margin": self._parse_float(data.get("ProfitMargin")) * 100 if data.get("ProfitMargin") else None,
                "operating_margin": self._parse_float(data.get("OperatingMarginTTM")) * 100 if data.get("OperatingMarginTTM") else None,
                "roe": self._parse_float(data.get("ReturnOnEquityTTM")) * 100 if data.get("ReturnOnEquityTTM") else None,
                "debt_to_equity": self._parse_float(data.get("DebtToEquityRatio")),
                "dividend_yield": self._parse_float(data.get("DividendYield")) * 100 if data.get("DividendYield") else None,
                "beta": self._parse_float(data.get("Beta")),
                "price_52w_high": self._parse_float(data.get("52WeekHigh")),
                "price_52w_low": self._parse_float(data.get("52WeekLow")),
                "current_price": self._parse_float(quote.get("05. price")),
                "next_earnings_date": None,  # Not available in free tier
            }
            
        except Exception as e:
            logger.warning(f"Alpha Vantage error for {ticker}: {e}")
            return None
    
    def _parse_float(self, value) -> Optional[float]:
        if value is None or value == "None" or value == "":
            return None
        try:
            return float(value)
        except:
            return None

# Singleton instance
alpha_vantage_client = AlphaVantageClient()
