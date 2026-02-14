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

class StockResponse(BaseModel):
    ticker: str
    name: str
    earnings: List[EarningsData]
    summary: StockSummaryData
