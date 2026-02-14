import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database import EarningsRecord, StockSummary
from app.services.mock_client import mock_client
from app.services.alpha_vantage_client import alpha_vantage_client
from app.services.finnhub_client import finnhub_client
import logging
import time
import os
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_HOURS = 24
MIN_REQUEST_INTERVAL = 2  # Minimum seconds between requests to Yahoo

class YFinanceClient:
    def __init__(self):
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Ensure we don't hit Yahoo's rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < MIN_REQUEST_INTERVAL:
            sleep_time = MIN_REQUEST_INTERVAL - elapsed + random.uniform(0.5, 1.5)
            logger.info(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _is_cache_fresh(self, fetched_at: datetime) -> bool:
        return datetime.utcnow() - fetched_at < timedelta(hours=CACHE_HOURS)
    
    def get_stock_data(self, ticker: str, db: Session) -> dict:
        """Get stock data with caching - tries multiple sources"""
        ticker = ticker.upper().strip()
        
        # Check if we have fresh cached data
        cached_summary = db.query(StockSummary).filter(
            StockSummary.ticker == ticker
        ).first()
        
        if cached_summary and self._is_cache_fresh(cached_summary.fetched_at):
            logger.info(f"Using cached data for {ticker}")
            cached_earnings = db.query(EarningsRecord).filter(
                EarningsRecord.ticker == ticker
            ).order_by(EarningsRecord.fiscal_date.desc()).all()
            
            return self._format_response(ticker, cached_summary, cached_earnings)
        
        # Try multiple data sources in order
        errors = []
        
        # Source 1: Yahoo Finance (yfinance) - best data
        try:
            logger.info(f"[Source 1/4] Trying Yahoo Finance for {ticker}")
            return self._fetch_and_cache(ticker, db)
        except Exception as e:
            errors.append(f"Yahoo: {str(e)[:50]}")
            logger.warning(f"Yahoo Finance failed: {e}")
        
        # Source 2: Finnhub (60 calls/min free)
        if finnhub_client.is_configured():
            try:
                logger.info(f"[Source 2/4] Trying Finnhub for {ticker}")
                fh_data = finnhub_client.get_stock_data(ticker)
                if fh_data:
                    return self._save_fallback_data(ticker, fh_data, db, "Finnhub")
            except Exception as e:
                errors.append(f"Finnhub: {str(e)[:50]}")
                logger.warning(f"Finnhub failed: {e}")
        else:
            logger.info("Finnhub not configured (no API key)")
        
        # Source 3: Alpha Vantage (5 calls/min free)
        if alpha_vantage_client.is_configured():
            try:
                logger.info(f"[Source 3/4] Trying Alpha Vantage for {ticker}")
                av_data = alpha_vantage_client.get_stock_data(ticker)
                if av_data:
                    return self._save_fallback_data(ticker, av_data, db, "AlphaVantage")
            except Exception as e:
                errors.append(f"AlphaVantage: {str(e)[:50]}")
                logger.warning(f"Alpha Vantage failed: {e}")
        else:
            logger.info("Alpha Vantage not configured (no API key)")
        
        # Source 4: Mock data (always works)
        logger.info(f"[Source 4/4] Using mock data for {ticker}")
        logger.warning(f"All real data sources failed: {'; '.join(errors)}")
        return mock_client.get_stock_data(ticker, db)
    
    def _save_fallback_data(self, ticker: str, data: dict, db: Session, source: str) -> dict:
        """Save fallback API data (Alpha Vantage or Finnhub) to database"""
        logger.info(f"Saving {source} data for {ticker}")
        
        # Clear old data
        db.query(StockSummary).filter(StockSummary.ticker == ticker).delete()
        db.query(EarningsRecord).filter(EarningsRecord.ticker == ticker).delete()
        
        # Create summary
        summary = StockSummary(
            ticker=ticker,
            name=data["name"],
            market_cap=data.get("market_cap"),
            pe_ratio=data.get("pe_ratio"),
            next_earnings_date=data.get("next_earnings_date"),
            profit_margin=data.get("profit_margin"),
            operating_margin=data.get("operating_margin"),
            roe=data.get("roe"),
            debt_to_equity=data.get("debt_to_equity"),
            dividend_yield=data.get("dividend_yield"),
            beta=data.get("beta"),
            price_52w_high=data.get("price_52w_high"),
            price_52w_low=data.get("price_52w_low"),
            current_price=data.get("current_price")
        )
        db.add(summary)
        
        # Create placeholder earnings (fallback APIs don't have historical earnings in free tier)
        # Generate 8 quarters of synthetic earnings based on current data
        now = datetime.utcnow()
        for i in range(8):
            quarter_date = now - timedelta(days=90 * (i + 1))
            quarter_end = self._get_quarter_end(quarter_date)
            
            # Estimate EPS from P/E and price
            price = data.get("current_price") or 100
            pe = data.get("pe_ratio") or 20
            estimated_eps = price / pe if pe and pe > 0 else 1.0
            
            # Add some variance
            variance = 1 + random.uniform(-0.2, 0.2)
            reported_eps = round(estimated_eps * variance * (8-i)/8, 2)
            
            record = EarningsRecord(
                ticker=ticker,
                fiscal_date=quarter_end.date(),
                period=self._get_period(quarter_end),
                reported_eps=reported_eps,
                estimated_eps=round(reported_eps * 0.95, 2),
                surprise_pct=round((reported_eps - reported_eps*0.95)/(reported_eps*0.95)*100, 2),
                revenue=None,  # Not available in free tier
                free_cash_flow=None,
                pe_ratio=data.get("pe_ratio"),
                price=price * (1 + random.uniform(-0.15, 0.15))
            )
            db.add(record)
        
        db.commit()
        db.refresh(summary)
        
        earnings = db.query(EarningsRecord).filter(
            EarningsRecord.ticker == ticker
        ).order_by(EarningsRecord.fiscal_date.desc()).all()
        
        return self._format_response(ticker, summary, earnings)
    
    def _fetch_and_cache(self, ticker: str, db: Session) -> dict:
        try:
            # Rate limit before making request
            self._rate_limit()
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Check if we got valid data
            if not info or info.get('regularMarketPrice') is None:
                raise ValueError(f"No data found for ticker {ticker}")
            
            # Get earnings dates
            earnings_df = stock.earnings_dates
            
            # Get quarterly income statement for revenue
            quarterly_income = stock.quarterly_income_stmt
            
            # Get quarterly cash flow for free cash flow
            quarterly_cashflow = stock.quarterly_cashflow
            
            # Get price history
            hist = stock.history(period="2y")
            
            # Extract earnings data with price and revenue
            earnings_records = self._parse_earnings(
                ticker, earnings_df, quarterly_income, quarterly_cashflow, hist, db
            )
            
            # Extract summary with all metrics
            summary = self._parse_summary(ticker, info, db)
            
            return self._format_response(ticker, summary, earnings_records)
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            raise
    
    def _parse_earnings(self, ticker: str, earnings_dates, quarterly_income, quarterly_cashflow, price_history, db: Session) -> List[EarningsRecord]:
        records = []
        
        try:
            if earnings_dates is not None and len(earnings_dates) > 0:
                # Clear old records
                db.query(EarningsRecord).filter(EarningsRecord.ticker == ticker).delete()
                
                for date, row in earnings_dates.head(12).iterrows():
                    try:
                        fiscal_date = date.date() if hasattr(date, 'date') else date
                        
                        # Get revenue for this quarter
                        revenue = self._get_metric_for_quarter(quarterly_income, 'Total Revenue', fiscal_date)
                        
                        # Get free cash flow for this quarter
                        fcf = self._get_metric_for_quarter(quarterly_cashflow, 'Free Cash Flow', fiscal_date)
                        
                        # Get stock price closest to earnings date
                        price = self._get_price_near_date(price_history, fiscal_date)
                        
                        # Calculate historical P/E if we have EPS and price
                        reported_eps = float(row.get('Reported EPS')) if pd.notna(row.get('Reported EPS')) else None
                        historical_pe = round(price / reported_eps, 2) if price and reported_eps and reported_eps > 0 else None
                        
                        record = EarningsRecord(
                            ticker=ticker,
                            fiscal_date=fiscal_date,
                            period=self._infer_period(date),
                            reported_eps=reported_eps,
                            estimated_eps=float(row.get('EPS Estimate')) if pd.notna(row.get('EPS Estimate')) else None,
                            surprise_pct=float(row.get('Surprise(%)')) if pd.notna(row.get('Surprise(%)')) else None,
                            revenue=revenue,
                            free_cash_flow=fcf,
                            pe_ratio=historical_pe,
                            price=price
                        )
                        db.add(record)
                        records.append(record)
                    except Exception as e:
                        logger.warning(f"Error parsing earnings row: {e}")
                        continue
                
                db.commit()
        except Exception as e:
            logger.error(f"Error parsing earnings: {e}")
            db.rollback()
        
        # Return from DB to ensure consistency
        return db.query(EarningsRecord).filter(
            EarningsRecord.ticker == ticker
        ).order_by(EarningsRecord.fiscal_date.desc()).all()
    
    def _get_metric_for_quarter(self, df, metric_name, target_date) -> Optional[float]:
        """Get a metric value for a specific quarter"""
        if df is None or metric_name not in df.index:
            return None
        
        try:
            # Find the closest quarter
            target = pd.Timestamp(target_date)
            closest_col = None
            min_diff = timedelta(days=365)
            
            for col in df.columns:
                if isinstance(col, (pd.Timestamp, datetime)):
                    diff = abs(col - target)
                    if diff < min_diff:
                        min_diff = diff
                        closest_col = col
            
            if closest_col and min_diff.days < 45:  # Within 45 days
                value = df.loc[metric_name, closest_col]
                return float(value) if pd.notna(value) else None
        except Exception as e:
            logger.warning(f"Error getting metric {metric_name}: {e}")
        
        return None
    
    def _get_price_near_date(self, price_history, target_date) -> Optional[float]:
        """Get stock price closest to a specific date"""
        if price_history is None or len(price_history) == 0:
            return None
        
        try:
            target = pd.Timestamp(target_date)
            
            # Find closest date in price history
            closest_idx = price_history.index.get_indexer([target], method='nearest')[0]
            if closest_idx >= 0:
                price = price_history.iloc[closest_idx]['Close']
                return float(price) if pd.notna(price) else None
        except Exception as e:
            logger.warning(f"Error getting price for date {target_date}: {e}")
        
        return None
    
    def _parse_summary(self, ticker: str, info: dict, db: Session) -> StockSummary:
        # Delete old summary
        db.query(StockSummary).filter(StockSummary.ticker == ticker).delete()
        
        next_earnings = None
        earnings_timestamp = info.get('earningsDate')
        if earnings_timestamp:
            try:
                if isinstance(earnings_timestamp, list) and len(earnings_timestamp) > 0:
                    next_earnings = datetime.fromtimestamp(earnings_timestamp[0]).date()
                elif isinstance(earnings_timestamp, (int, float)):
                    next_earnings = datetime.fromtimestamp(earnings_timestamp).date()
            except Exception as e:
                logger.warning(f"Could not parse earnings date: {e}")
        
        summary = StockSummary(
            ticker=ticker,
            name=info.get('longName') or info.get('shortName', ticker),
            market_cap=info.get('marketCap'),
            pe_ratio=info.get('trailingPE') or info.get('forwardPE'),
            next_earnings_date=next_earnings,
            profit_margin=info.get('profitMargins', 0) * 100 if info.get('profitMargins') else None,
            operating_margin=info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else None,
            roe=info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else None,
            debt_to_equity=info.get('debtToEquity'),
            dividend_yield=info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            beta=info.get('beta'),
            price_52w_high=info.get('fiftyTwoWeekHigh'),
            price_52w_low=info.get('fiftyTwoWeekLow'),
            current_price=info.get('currentPrice') or info.get('regularMarketPrice')
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        return summary
    
    def _infer_period(self, date) -> str:
        """Infer fiscal quarter from date"""
        if hasattr(date, 'month'):
            month = date.month
        else:
            return "Q"
        
        if month in [1, 2, 3]:
            return "Q1"
        elif month in [4, 5, 6]:
            return "Q2"
        elif month in [7, 8, 9]:
            return "Q3"
        else:
            return "Q4"
    
    def _format_response(self, ticker: str, summary: StockSummary, earnings: List[EarningsRecord]) -> dict:
        return {
            "ticker": ticker,
            "name": summary.name,
            "summary": {
                "ticker": ticker,
                "name": summary.name,
                "market_cap": summary.market_cap,
                "pe_ratio": summary.pe_ratio,
                "next_earnings_date": summary.next_earnings_date.isoformat() if summary.next_earnings_date else None,
                "profit_margin": summary.profit_margin,
                "operating_margin": summary.operating_margin,
                "roe": summary.roe,
                "debt_to_equity": summary.debt_to_equity,
                "dividend_yield": summary.dividend_yield,
                "beta": summary.beta,
                "price_52w_high": summary.price_52w_high,
                "price_52w_low": summary.price_52w_low,
                "current_price": summary.current_price
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
            ]
        }

yfinance_client = YFinanceClient()
