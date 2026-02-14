import random
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from app.database import EarningsRecord, StockSummary
import logging

logger = logging.getLogger(__name__)

# Mock data for popular tickers
MOCK_COMPANIES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "NVDA": "NVIDIA Corporation",
    "TSLA": "Tesla Inc.",
    "META": "Meta Platforms Inc.",
    "NFLX": "Netflix Inc.",
}

class MockDataClient:
    """Mock client for testing when real APIs are rate-limited"""
    
    def get_stock_data(self, ticker: str, db: Session) -> dict:
        ticker = ticker.upper().strip()
        
        # Check cache first
        cached_summary = db.query(StockSummary).filter(
            StockSummary.ticker == ticker
        ).first()
        
        if cached_summary:
            cached_earnings = db.query(EarningsRecord).filter(
                EarningsRecord.ticker == ticker
            ).order_by(EarningsRecord.fiscal_date.desc()).all()
            return self._format_response(ticker, cached_summary, cached_earnings)
        
        return self._generate_mock_data(ticker, db)
    
    def _generate_mock_data(self, ticker: str, db: Session) -> dict:
        name = MOCK_COMPANIES.get(ticker, f"{ticker} Corporation")
        
        # Generate consistent "random" values based on ticker
        seed = sum(ord(c) for c in ticker)
        random.seed(seed)
        
        base_eps = random.uniform(0.5, 5.0)
        base_revenue = random.uniform(10e9, 100e9)
        market_cap = random.uniform(100e9, 3000e9)
        pe_ratio = random.uniform(15.0, 45.0)
        
        # Generate 8 quarters of earnings
        earnings = []
        now = datetime.utcnow()
        
        # Clear old data
        db.query(EarningsRecord).filter(EarningsRecord.ticker == ticker).delete()
        
        for i in range(8):
            quarter_date = now - timedelta(days=90 * (i + 1))
            quarter_end = self._get_quarter_end(quarter_date)
            
            # Add some realistic variance
            growth_factor = 1 + (random.uniform(-0.1, 0.15) * (8 - i) / 8)
            reported = round(base_eps * growth_factor * (1 + random.uniform(-0.05, 0.05)), 2)
            estimated = round(reported * (1 + random.uniform(-0.08, 0.02)), 2)
            surprise = round((reported - estimated) / estimated * 100, 2) if estimated != 0 else 0
            
            # Generate historical P/E (tends to fluctuate with sentiment)
            base_pe = random.uniform(15.0, 35.0)
            historical_pe = round(base_pe * (1 + random.uniform(-0.2, 0.2)), 2)
            
            # FCF is typically less than revenue (roughly 15-30% for tech)
            fcf_margin = random.uniform(0.15, 0.30)
            fcf = round(base_revenue * growth_factor * fcf_margin, 0)
            
            record = EarningsRecord(
                ticker=ticker,
                fiscal_date=quarter_end.date(),
                period=self._get_period(quarter_end),
                reported_eps=reported,
                estimated_eps=estimated,
                surprise_pct=surprise,
                revenue=round(base_revenue * growth_factor, 0),
                free_cash_flow=fcf,
                pe_ratio=historical_pe
            )
            db.add(record)
            earnings.append(record)
        
        # Create summary with additional metrics
        db.query(StockSummary).filter(StockSummary.ticker == ticker).delete()
        next_earnings = (now + timedelta(days=random.randint(15, 90))).date()
        
        # Generate additional financial metrics
        profit_margin = round(random.uniform(0.10, 0.35) * 100, 2)  # 10-35%
        operating_margin = round(profit_margin + random.uniform(2, 8), 2)  # Slightly higher than profit margin
        roe = round(random.uniform(0.15, 0.45) * 100, 2)  # 15-45%
        debt_to_equity = round(random.uniform(0.1, 1.5), 2)  # 0.1x to 1.5x
        dividend_yield = round(random.uniform(0, 0.05) * 100, 2) if random.random() > 0.3 else 0  # 0-5%, 30% don't pay dividends
        beta = round(random.uniform(0.5, 2.0), 2)  # 0.5 (stable) to 2.0 (volatile)
        current_price = round(random.uniform(50, 800), 2)
        price_52w_high = round(current_price * random.uniform(1.1, 1.5), 2)
        price_52w_low = round(current_price * random.uniform(0.5, 0.9), 2)
        
        summary = StockSummary(
            ticker=ticker,
            name=name,
            market_cap=market_cap,
            pe_ratio=pe_ratio,
            next_earnings_date=next_earnings,
            profit_margin=profit_margin,
            operating_margin=operating_margin,
            roe=roe,
            debt_to_equity=debt_to_equity,
            dividend_yield=dividend_yield,
            beta=beta,
            price_52w_high=price_52w_high,
            price_52w_low=price_52w_low,
            current_price=current_price
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        
        return self._format_response(ticker, summary, earnings)
    
    def _get_quarter_end(self, date: datetime) -> datetime:
        """Get the last day of the quarter for a given date"""
        year = date.year
        month = date.month
        
        if month <= 3:
            return datetime(year, 3, 31)
        elif month <= 6:
            return datetime(year, 6, 30)
        elif month <= 9:
            return datetime(year, 9, 30)
        else:
            return datetime(year, 12, 31)
    
    def _get_period(self, date: datetime) -> str:
        month = date.month
        if month <= 3:
            return "Q1"
        elif month <= 6:
            return "Q2"
        elif month <= 9:
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
                    "pe_ratio": e.pe_ratio
                }
                for e in sorted(earnings, key=lambda x: x.fiscal_date, reverse=True)
            ]
        }

mock_client = MockDataClient()
