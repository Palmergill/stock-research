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
            
            # 5. Get 1-year daily price history for chart
            price_history = self._get_price_history(ticker, days=365)
            
            # 6. Build earnings history from financials
            earnings = self._build_earnings_from_financials(financials)
            
            # 6. Calculate additional metrics
            revenue_growth = self._calculate_revenue_growth(financials)
            latest_fcf = self._get_latest_fcf(financials)
            
            # Calculate margins from financial data
            profit_margin = self._calculate_profit_margin(financials)
            operating_margin = self._calculate_operating_margin(financials)
            
            return {
                "name": details.get("name", ticker),
                "ticker": ticker,
                "market_cap": details.get("market_cap"),
                "current_price": price_data.get("close"),
                "pe_ratio": self._calculate_pe(details, price_data, earnings),
                "revenue_growth": revenue_growth,
                "free_cash_flow": latest_fcf,
                "debt_to_equity": self._extract_metric(financials, "debt_to_equity"),
                "roe": self._extract_metric(financials, "return_on_equity"),
                "price_52w_high": year_high_low.get("high"),
                "price_52w_low": year_high_low.get("low"),
                "profit_margin": profit_margin,
                "operating_margin": operating_margin,
                "dividend_yield": details.get("dividend_yield"),
                "beta": details.get("beta"),  # May be available in some tickers
                "next_earnings_date": None,  # Requires different endpoint
                "earnings": earnings,
                "price_history": price_history,  # 1-year daily prices
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
    
    def _get_price_history(self, ticker: str, days: int = 365) -> List[Dict]:
        """Get daily price history for the specified number of days"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = f"{self.BASE_URL}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {
                "adjusted": "true",
                "sort": "asc",
                "apiKey": self.api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                # Return simplified price data
                return [
                    {
                        "date": datetime.fromtimestamp(r["t"] / 1000).strftime("%Y-%m-%d"),
                        "open": r.get("o"),
                        "high": r.get("h"),
                        "low": r.get("l"),
                        "close": r.get("c"),
                        "volume": r.get("v")
                    }
                    for r in data["results"]
                    if r.get("c")  # Only include if we have a close price
                ]
            return []
        except Exception as e:
            logger.warning(f"Could not fetch price history for {ticker}: {e}")
            return []
    
    def _build_earnings_from_financials(self, financials: List[Dict]) -> List[Dict]:
        """Build earnings records from financial statements"""
        earnings = []
        
        for i, fin in enumerate(financials[:8]):  # Last 8 quarters
            try:
                fiscal_date = fin.get("filing_date") or fin.get("period_of_report_date") or fin.get("end_date")
                if not fiscal_date:
                    continue
                
                # Extract financial data with multiple field name possibilities
                financials_data = fin.get("financials", {})
                income = financials_data.get("income_statement", {}) or {}
                balance = financials_data.get("balance_sheet", {}) or {}
                cash_flow = financials_data.get("cash_flow_statement", {}) or {}
                
                # Get revenue with multiple possible field names
                revenue = None
                for rev_key in ["revenues", "total_revenue", "revenue"]:
                    rev_data = income.get(rev_key)
                    if isinstance(rev_data, dict):
                        revenue = rev_data.get("value")
                    elif rev_data is not None:
                        revenue = rev_data
                    if revenue:
                        break
                
                # Get EPS directly from income statement (Polygon provides this!)
                eps = None
                for eps_key in ["basic_earnings_per_share", "diluted_earnings_per_share", "earnings_per_share"]:
                    eps_data = income.get(eps_key)
                    if isinstance(eps_data, dict):
                        eps = eps_data.get("value")
                    elif eps_data is not None:
                        eps = eps_data
                    if eps:
                        break
                
                # Get FCF
                fcf = None
                for fcf_key in ["net_cash_flow_from_operating_activities", "operating_cash_flow", "free_cash_flow"]:
                    fcf_data = cash_flow.get(fcf_key)
                    if isinstance(fcf_data, dict):
                        fcf = fcf_data.get("value")
                    elif fcf_data is not None:
                        fcf = fcf_data
                    if fcf:
                        break
                
                earnings.append({
                    "fiscal_date": fiscal_date,
                    "period": self._get_quarter_from_date(fiscal_date),
                    "reported_eps": eps,
                    "estimated_eps": None,
                    "surprise_pct": None,
                    "revenue": revenue,
                    "free_cash_flow": fcf,
                    "pe_ratio": None,
                    "price": None
                })
            except Exception as e:
                logger.warning(f"Error processing financial {i}: {e}")
                continue
        
        return earnings
    
    def _calculate_pe(self, details: Dict, price_data: Dict, earnings: List[Dict]) -> Optional[float]:
        """Calculate P/E ratio from price and TTM earnings"""
        try:
            price = price_data.get("close")
            if not price:
                logger.warning("No price available for P/E calculation")
                return None
            
            # Calculate TTM EPS from earnings records
            if earnings and len(earnings) >= 4:
                total_eps = 0
                quarters_with_eps = 0
                
                for i, e in enumerate(earnings[:4]):  # Last 4 quarters
                    eps = e.get("reported_eps")
                    logger.info(f"Q{i}: reported_eps={eps}")
                    
                    if eps and eps > 0:
                        total_eps += eps
                        quarters_with_eps += 1
                
                logger.info(f"Total TTM EPS: {total_eps} from {quarters_with_eps} quarters, price={price}")
                if quarters_with_eps >= 3 and total_eps > 0:  # Allow 3+ quarters for recent IPOs
                    pe = round(price / total_eps, 2)
                    logger.info(f"Calculated P/E: {pe}")
                    return pe
            else:
                logger.warning(f"Not enough earnings: {len(earnings) if earnings else 0}")
                    
        except Exception as e:
            logger.warning(f"Could not calculate P/E: {e}")
        return None
    
    def _calculate_revenue_growth(self, financials: List[Dict]) -> Optional[float]:
        """Calculate YoY revenue growth rate (%)"""
        try:
            if len(financials) < 5:
                return None
            
            # Get latest quarter revenue
            latest = financials[0].get("financials", {}).get("income_statement", {}).get("revenues", {})
            latest_rev = latest.get("value") if isinstance(latest, dict) else None
            
            # Get same quarter last year (4 quarters back)
            year_ago = financials[4].get("financials", {}).get("income_statement", {}).get("revenues", {})
            year_ago_rev = year_ago.get("value") if isinstance(year_ago, dict) else None
            
            if latest_rev and year_ago_rev and year_ago_rev > 0:
                growth = ((latest_rev - year_ago_rev) / year_ago_rev) * 100
                return round(growth, 2)
        except Exception as e:
            logger.warning(f"Could not calculate revenue growth: {e}")
        return None
    
    def _get_latest_fcf(self, financials: List[Dict]) -> Optional[float]:
        """Get latest quarter free cash flow"""
        try:
            if not financials:
                return None
            
            fin = financials[0].get("financials", {})
            cash_flow = fin.get("cash_flow_statement", {})
            
            # Try FCF field first, then operating cash flow
            for key in ["free_cash_flow", "net_cash_flow_from_operating_activities"]:
                fcf_data = cash_flow.get(key)
                if isinstance(fcf_data, dict):
                    return fcf_data.get("value")
                elif fcf_data is not None:
                    return fcf_data
        except Exception as e:
            logger.warning(f"Could not get FCF: {e}")
        return None
    
    def _extract_metric(self, financials: List[Dict], metric_name: str) -> Optional[float]:
        """Extract a metric from most recent financial statement"""
        if not financials:
            return None
        
        try:
            fin = financials[0]
            financials_data = fin.get("financials", {})
            
            # Try different possible field names based on Polygon's schema
            metric_map = {
                "profit_margin": [
                    ("income_statement", "net_profit_margin"),
                    ("income_statement", "profit_margin"),
                ],
                "operating_margin": [
                    ("income_statement", "operating_income_margin"),
                    ("income_statement", "operating_margin"),
                ],
                "return_on_equity": [
                    ("financial_metrics", "return_on_equity"),
                    ("financial_metrics", "roe"),
                ],
                "debt_to_equity": [
                    ("financial_metrics", "debt_to_equity_ratio"),
                    ("financial_metrics", "debt_equity_ratio"),
                ]
            }
            
            if metric_name in metric_map:
                for section, key in metric_map[metric_name]:
                    try:
                        section_data = financials_data.get(section, {})
                        if isinstance(section_data, dict):
                            value_data = section_data.get(key)
                            if isinstance(value_data, dict):
                                value = value_data.get("value")
                            else:
                                value = value_data
                            if value is not None:
                                return float(value)
                    except:
                        continue
            
            # Calculate ROE and Debt-to-Equity from balance sheet if not found
            if metric_name == "return_on_equity":
                return self._calculate_roe(financials_data)
            elif metric_name == "debt_to_equity":
                return self._calculate_debt_to_equity(financials_data)
                
        except Exception as e:
            logger.warning(f"Error extracting metric {metric_name}: {e}")
        
        return None
    
    def _calculate_roe(self, financials_data: Dict) -> Optional[float]:
        """Calculate ROE = Net Income / Shareholder Equity"""
        try:
            income = financials_data.get("income_statement", {})
            balance = financials_data.get("balance_sheet", {})
            
            # Get net income
            net_income = None
            for key in ["net_income_loss", "net_income", "net_income_loss_attributable_to_parent"]:
                ni_data = income.get(key)
                if isinstance(ni_data, dict):
                    net_income = ni_data.get("value")
                elif ni_data is not None:
                    net_income = ni_data
                if net_income is not None:
                    break
            
            # Get equity
            equity = None
            for key in ["equity", "equity_attributable_to_parent", "stockholders_equity"]:
                eq_data = balance.get(key)
                if isinstance(eq_data, dict):
                    equity = eq_data.get("value")
                elif eq_data is not None:
                    equity = eq_data
                if equity is not None:
                    break
            
            logger.info(f"ROE calc: net_income={net_income}, equity={equity}")
            
            if net_income is not None and equity and equity > 0:
                roe = (net_income / equity) * 100  # Return as percentage
                logger.info(f"Calculated ROE: {roe}")
                return round(roe, 2)
        except Exception as e:
            logger.warning(f"Could not calculate ROE: {e}")
        return None
    
    def _calculate_debt_to_equity(self, financials_data: Dict) -> Optional[float]:
        """Calculate Debt-to-Equity = Total Liabilities / Shareholder Equity"""
        try:
            balance = financials_data.get("balance_sheet", {})
            
            # Get total liabilities
            liabilities = None
            for key in ["liabilities", "total_liabilities"]:
                liab_data = balance.get(key)
                if isinstance(liab_data, dict):
                    liabilities = liab_data.get("value")
                elif liab_data is not None:
                    liabilities = liab_data
                if liabilities is not None:
                    break
            
            # Get equity
            equity = None
            for key in ["equity", "equity_attributable_to_parent", "stockholders_equity"]:
                eq_data = balance.get(key)
                if isinstance(eq_data, dict):
                    equity = eq_data.get("value")
                elif eq_data is not None:
                    equity = eq_data
                if equity is not None:
                    break
            
            logger.info(f"D/E calc: liabilities={liabilities}, equity={equity}")
            
            if liabilities is not None and equity and equity > 0:
                dte = liabilities / equity
                logger.info(f"Calculated D/E: {dte}")
                return round(dte, 2)
        except Exception as e:
            logger.warning(f"Could not calculate D/E: {e}")
        return None
    
    def _calculate_profit_margin(self, financials: List[Dict]) -> Optional[float]:
        """Calculate profit margin from latest financial: Net Income / Revenue * 100"""
        try:
            if not financials:
                return None
            
            fin = financials[0].get("financials", {})
            income = fin.get("income_statement", {})
            
            # Get net income
            net_income = None
            for key in ["net_income_loss", "net_income", "net_income_loss_attributable_to_parent"]:
                ni_data = income.get(key)
                if isinstance(ni_data, dict):
                    net_income = ni_data.get("value")
                elif ni_data is not None:
                    net_income = ni_data
                if net_income is not None:
                    break
            
            # Get revenue
            revenue = None
            for key in ["revenues", "total_revenue", "revenue"]:
                rev_data = income.get(key)
                if isinstance(rev_data, dict):
                    revenue = rev_data.get("value")
                elif rev_data is not None:
                    revenue = rev_data
                if revenue:
                    break
            
            if net_income is not None and revenue and revenue > 0:
                margin = (net_income / revenue) * 100
                return round(margin, 2)
        except Exception as e:
            logger.warning(f"Could not calculate profit margin: {e}")
        return None
    
    def _calculate_operating_margin(self, financials: List[Dict]) -> Optional[float]:
        """Calculate operating margin: Operating Income / Revenue * 100"""
        try:
            if not financials:
                return None
            
            fin = financials[0].get("financials", {})
            income = fin.get("income_statement", {})
            
            # Get operating income
            op_income = None
            for key in ["operating_income_loss", "operating_income"]:
                op_data = income.get(key)
                if isinstance(op_data, dict):
                    op_income = op_data.get("value")
                elif op_data is not None:
                    op_income = op_data
                if op_income is not None:
                    break
            
            # Get revenue
            revenue = None
            for key in ["revenues", "total_revenue", "revenue"]:
                rev_data = income.get(key)
                if isinstance(rev_data, dict):
                    revenue = rev_data.get("value")
                elif rev_data is not None:
                    revenue = rev_data
                if revenue:
                    break
            
            if op_income is not None and revenue and revenue > 0:
                margin = (op_income / revenue) * 100
                return round(margin, 2)
        except Exception as e:
            logger.warning(f"Could not calculate operating margin: {e}")
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
