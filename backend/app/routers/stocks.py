from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.yfinance_client import yfinance_client

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

@router.get("/{ticker}")
async def get_stock(ticker: str, db: Session = Depends(get_db)):
    """Get stock data including earnings and summary"""
    try:
        data = yfinance_client.get_stock_data(ticker, db)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}: {str(e)}")

@router.get("/{ticker}/earnings")
async def get_earnings(ticker: str, db: Session = Depends(get_db)):
    """Get earnings data for a ticker"""
    try:
        data = yfinance_client.get_stock_data(ticker, db)
        return {"ticker": ticker, "earnings": data["earnings"]}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch earnings for {ticker}: {str(e)}")
