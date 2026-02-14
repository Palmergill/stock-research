from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class EarningsData(BaseModel):
    fiscal_date: date
    period: str
    reported_eps: Optional[float]
    estimated_eps: Optional[float]
    surprise_pct: Optional[float]
    revenue: Optional[float]
    free_cash_flow: Optional[float]
    pe_ratio: Optional[float]

class StockSummaryData(BaseModel):
    ticker: str
    name: str
    market_cap: Optional[float]
    pe_ratio: Optional[float]
    next_earnings_date: Optional[date]
    # Additional metrics
    profit_margin: Optional[float]  # Net income / Revenue
    operating_margin: Optional[float]  # Operating income / Revenue
    roe: Optional[float]  # Return on equity
    debt_to_equity: Optional[float]  # Debt / Equity ratio
    dividend_yield: Optional[float]  # Annual dividend / Price
    beta: Optional[float]  # Stock volatility vs market
    price_52w_high: Optional[float]  # 52 week high
    price_52w_low: Optional[float]  # 52 week low
    current_price: Optional[float]  # Current stock price

class StockResponse(BaseModel):
    ticker: str
    name: str
    earnings: List[EarningsData]
    summary: StockSummaryData
