import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os
import logging

logger = logging.getLogger(__name__)

class PolygonClient:
    """Polygon.io API client - primary data source"""
    
    BASE_URL = "https://api.polygon.io"
    
    def __init__(self):
        self.api_key = os.getenv("POLYGON_API_KEY")
    
    def is_configured(self) -> bool:
        return self.api_key is not None and self.api_key != ""
    
    def get_stock_data(self, ticker: str) -> Optional[Dict]:
        """Fetch complete stock data from Polygon.io"""
        if not self.is_configured():
            raise ValueError("Polygon API key not configured")
        
        ticker = ticker.upper()
        
        try:
            # 1. Get ticker details
            details = self._get_ticker_details(ticker)
            
            # 2. Get current price / previous close
            price_data = self._get_previous_close(ticker)
            
            # 3. Get financials (quarterly)
            financials = self._get_financials(ticker)
            
            # 4. Get historical price for 52-week range
            year_high_low = self._get_52_week_range(ticker)
            
            # 5. Build earnings history from financials
            earnings = self._build_earnings_from_financials(financials)
            
            return {
                "name": details.get("name", ticker),
                "ticker": ticker,
                "market_cap": details.get("market_cap"),
                "current_price": price_data.get("close"),
                "pe_ratio": self._calculate_pe(details, price_data),
                "price_52w_high": year_high_low.get("high"),
                "price_52w_low": year_high_low.get("low"),
                "profit_margin": self._extract_metric(financials, "profit_margin"),
                "operating_margin": self._extract_metric(financials, "operating_margin"),
                "roe": self._extract_metric(financials, "return_on_equity"),
                "debt_to_equity": self._extract_metric(financials, "debt_to_equity"),
                "dividend_yield": details.get("dividend_yield"),
                "beta": None,  # Not directly available
                "next_earnings_date": None,  # Not available in API
                "earnings": earnings,
                "source": "Polygon.io"
            }
            
        except Exception as e:
            logger.error(f"Polygon.io error for {ticker}: {e}")
            raise
    
    def _get_ticker_details(self, ticker: str) -> Dict:
        """Get company details"""
        url = f"{self.BASE_URL}/v3/reference/tickers/{ticker}"
        response = requests.get(url, params={"apiKey": self.api_key}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "OK" or not data.get("results"):
            raise ValueError(f"Ticker {ticker} not found")
        
        return data["results"]
    
    def _get_previous_close(self, ticker: str) -> Dict:
        """Get previous day's close price"""
        url = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/prev"
        response = requests.get(url, params={"apiKey": self.api_key}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("results") and len(data["results"]) > 0:
            result = data["results"][0]
            return {
                "open": result.get("o"),
                "high": result.get("h"),
                "low": result.get("l"),
                "close": result.get("c"),
                "volume": result.get("v")
            }
        return {}
    
    def _get_financials(self, ticker: str) -> List[Dict]:
        """Get quarterly financial statements"""
        url = f"{self.BASE_URL}/vX/reference/financials"
        params = {
            "ticker": ticker,
            "timeframe": "quarterly",
            "order": "desc",
            "limit": 12,
            "apiKey": self.api_key
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data.get("results", [])
    
    def _get_52_week_range(self, ticker: str) -> Dict:
        """Get 52-week high/low from aggregates"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        url = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
        params = {
            "adjusted": "true",
            "sort": "asc",
            "apiKey": self.api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("results") and len(data["results"]) > 0:
            highs = [r.get("h") for r in data["results"] if r.get("h")]
            lows = [r.get("l") for r in data["results"] if r.get("l")]
            return {
                "high": max(highs) if highs else None,
                "low": min(lows) if lows else None
            }
        return {}
    
    def _build_earnings_from_financials(self, financials: List[Dict]) -> List[Dict]:
        """Build earnings records from financial statements"""
        earnings = []
        
        for i, fin in enumerate(financials[:8]):  # Last 8 quarters
            try:
                fiscal_date = fin.get("filing_date") or fin.get("period_of_report_date")
                if not fiscal_date:
                    continue
                
                # Extract financial data
                financials_data = fin.get("financials", {})
                income = financials_data.get("income_statement", {})
                balance = financials_data.get("balance_sheet", {})
                cash_flow = financials_data.get("cash_flow_statement", {})
                
                # Calculate EPS if available
                net_income = income.get("net_income_loss", {}).get("value")
                shares = balance.get("shares", {}).get("value")
                eps = net_income / shares if net_income and shares else None
                
                earnings.append({
                    "fiscal_date": fiscal_date,
                    "period": self._get_quarter_from_date(fiscal_date),
                    "reported_eps": eps,
                    "estimated_eps": None,  # Not available in Polygon
                    "surprise_pct": None,  # Not available in Polygon
                    "revenue": income.get("revenues", {}).get("value"),
                    "free_cash_flow": cash_flow.get("net_cash_flow_from_operating_activities", {}).get("value"),
                    "pe_ratio": None,  # Will be calculated later
                    "price": None  # Will be filled in later
                })
            except Exception as e:
                logger.warning(f"Error processing financial {i}: {e}")
                continue
        
        return earnings
    
    def _calculate_pe(self, details: Dict, price_data: Dict) -> Optional[float]:
        """Calculate P/E ratio from price and earnings"""
        try:
            price = price_data.get("close")
            # Use basic EPS from details if available
            eps = details.get("eps") or details.get("earnings_per_share")
            if price and eps and eps > 0:
                return price / eps
        except:
            pass
        return None
    
    def _extract_metric(self, financials: List[Dict], metric_name: str) -> Optional[float]:
        """Extract a metric from most recent financial statement"""
        if not financials:
            return None
        
        try:
            fin = financials[0]
            financials_data = fin.get("financials", {})
            
            metric_map = {
                "profit_margin": ("income_statement", "net_profit_margin"),
                "operating_margin": ("income_statement", "operating_income_margin"),
                "return_on_equity": ("financial_metrics", "return_on_equity"),
                "debt_to_equity": ("financial_metrics", "debt_to_equity_ratio")
            }
            
            if metric_name in metric_map:
                section, key = metric_map[metric_name]
                value = financials_data.get(section, {}).get(key, {}).get("value")
                return value
        except:
            pass
        
        return None
    
    def _get_quarter_from_date(self, date_str: str) -> str:
        """Extract quarter from date string"""
        try:
            if isinstance(date_str, str):
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                date = date_str
            
            month = date.month
            if month <= 3:
                return "Q1"
            elif month <= 6:
                return "Q2"
            elif month <= 9:
                return "Q3"
            else:
                return "Q4"
        except:
            return "Q"

# Singleton instance
polygon_client = PolygonClient()
