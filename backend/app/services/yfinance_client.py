import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from app.database import EarningsRecord, StockSummary
from app.services.mock_client import mock_client
import logging
import time
import requests
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CACHE_HOURS = 24

class YFinanceClient:
    def __init__(self):
        # Configure yfinance session with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def _is_cache_fresh(self, fetched_at: datetime) -> bool:
        return datetime.utcnow() - fetched_at < timedelta(hours=CACHE_HOURS)
    
    def get_stock_data(self, ticker: str, db: Session) -> dict:
        """Get stock data with caching"""
        ticker = ticker.upper().strip()
        
        # Use mock data if env var set or yfinance is failing
        if os.getenv("USE_MOCK_DATA", "true").lower() == "true":
            logger.info(f"Using mock data for {ticker}")
            return mock_client.get_stock_data(ticker, db)
        
        # Check if we have fresh data
        cached_summary = db.query(StockSummary).filter(
            StockSummary.ticker == ticker
        ).first()
        
        if cached_summary and self._is_cache_fresh(cached_summary.fetched_at):
            logger.info(f"Using cached data for {ticker}")
            cached_earnings = db.query(EarningsRecord).filter(
                EarningsRecord.ticker == ticker
            ).order_by(EarningsRecord.fiscal_date.desc()).all()
            
            return self._format_response(ticker, cached_summary, cached_earnings)
        
        # Fetch fresh data with retry
        logger.info(f"Fetching fresh data for {ticker}")
        return self._fetch_with_retry(ticker, db)
    
    def _fetch_with_retry(self, ticker: str, db: Session, max_retries: int = 3) -> dict:
        for attempt in range(max_retries):
            try:
                return self._fetch_and_cache(ticker, db)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Attempt {attempt + 1} failed for {ticker}, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        raise Exception(f"Failed to fetch {ticker} after {max_retries} attempts")
    
    def _fetch_and_cache(self, ticker: str, db: Session) -> dict:
        try:
            stock = yf.Ticker(ticker, session=self.session)
            info = stock.info
            
            # Check if we got valid data
            if not info or info.get('regularMarketPrice') is None:
                raise ValueError(f"No data found for ticker {ticker}")
            
            # Get earnings dates
            earnings_df = stock.earnings_dates
            
            # Extract earnings data
            earnings_records = self._parse_earnings(ticker, earnings_df, db)
            
            # Extract summary
            summary = self._parse_summary(ticker, info, db)
            
            return self._format_response(ticker, summary, earnings_records)
            
        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {e}")
            raise
    
    def _parse_earnings(self, ticker: str, earnings_dates, db: Session) -> List[EarningsRecord]:
        records = []
        
        try:
            if earnings_dates is not None and len(earnings_dates) > 0:
                # Clear old records
                db.query(EarningsRecord).filter(EarningsRecord.ticker == ticker).delete()
                
                for date, row in earnings_dates.head(12).iterrows():
                    try:
                        record = EarningsRecord(
                            ticker=ticker,
                            fiscal_date=date.date() if hasattr(date, 'date') else date,
                            period=self._infer_period(date),
                            reported_eps=float(row.get('Reported EPS')) if pd.notna(row.get('Reported EPS')) else None,
                            estimated_eps=float(row.get('EPS Estimate')) if pd.notna(row.get('EPS Estimate')) else None,
                            surprise_pct=float(row.get('Surprise(%)')) if pd.notna(row.get('Surprise(%)')) else None,
                            revenue=None
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
            next_earnings_date=next_earnings
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
                "next_earnings_date": summary.next_earnings_date.isoformat() if summary.next_earnings_date else None
            },
            "earnings": [
                {
                    "fiscal_date": e.fiscal_date.isoformat(),
                    "period": e.period,
                    "reported_eps": e.reported_eps,
                    "estimated_eps": e.estimated_eps,
                    "surprise_pct": e.surprise_pct,
                    "revenue": e.revenue
                }
                for e in sorted(earnings, key=lambda x: x.fiscal_date, reverse=True)
            ]
        }

yfinance_client = YFinanceClient()
