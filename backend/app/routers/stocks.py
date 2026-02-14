from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.yfinance_client import yfinance_client
from app.services.stock_data import search_stocks

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

@router.get("/search")
async def search_stocks_endpoint(q: str = Query(..., min_length=1), limit: int = 10):
    """Search stocks by ticker or company name"""
    results = search_stocks(q, limit)
    return {"results": results, "query": q}

@router.get("/{ticker}")
async def get_stock(ticker: str, refresh: bool = False, db: Session = Depends(get_db)):
    """Get stock data including earnings and summary"""
    try:
        data = yfinance_client.get_stock_data(ticker, db, force_refresh=refresh)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}: {str(e)}")

@router.post("/{ticker}/refresh")
async def refresh_stock(ticker: str, db: Session = Depends(get_db)):
    """Force refresh stock data (bypass cache)"""
    try:
        data = yfinance_client.get_stock_data(ticker, db, force_refresh=True)
        return {"success": True, "message": f"Refreshed data for {ticker}", "data": data}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not refresh data for {ticker}: {str(e)}")

@router.get("/{ticker}/earnings")
async def get_earnings(ticker: str, db: Session = Depends(get_db)):
    """Get earnings data for a ticker"""
    try:
        data = yfinance_client.get_stock_data(ticker, db)
        return {"ticker": ticker, "earnings": data["earnings"]}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch earnings for {ticker}: {str(e)}")
