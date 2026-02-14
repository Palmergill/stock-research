from sqlalchemy import create_engine, Column, String, Float, Date, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stock_data.db")

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class EarningsRecord(Base):
    __tablename__ = "earnings"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    fiscal_date = Column(Date)
    period = Column(String)  # Q1, Q2, Q3, Q4, FY
    reported_eps = Column(Float, nullable=True)
    estimated_eps = Column(Float, nullable=True)
    surprise_pct = Column(Float, nullable=True)
    revenue = Column(Float, nullable=True)
    free_cash_flow = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)  # Historical P/E at time of earnings
    price = Column(Float, nullable=True)  # Stock price at time of earnings
    fetched_at = Column(DateTime, default=datetime.utcnow)

class StockSummary(Base):
    __tablename__ = "stock_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True, unique=True)
    name = Column(String)
    market_cap = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    next_earnings_date = Column(Date, nullable=True)
    # Additional metrics
    profit_margin = Column(Float, nullable=True)
    operating_margin = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)
    dividend_yield = Column(Float, nullable=True)
    beta = Column(Float, nullable=True)
    price_52w_high = Column(Float, nullable=True)
    price_52w_low = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
