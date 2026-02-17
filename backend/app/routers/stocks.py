from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import os
from app.database import get_db
from app.services.stock_data_client import stock_data_client
from app.services.stock_data import search_stocks
from app.services.polygon_client import polygon_client
from app.services.finnhub_client import finnhub_estimates_client

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

@router.get("/search")
async def search_stocks_endpoint(q: str = Query(..., min_length=1), limit: int = 10):
    """Search stocks by ticker or company name"""
    # Use mock search if not using real data
    if stock_data_client._use_mock():
        results = stock_data_client.mock.search_stocks(q, limit)
    else:
        results = search_stocks(q, limit)
    return {"results": results, "query": q}

@router.get("/{ticker}/debug/finnhub")
async def debug_finnhub(ticker: str):
    """Debug endpoint to see raw Finnhub earnings data"""
    try:
        if not finnhub_estimates_client.is_configured():
            return {"error": "Finnhub API key not configured"}
        
        estimates = finnhub_estimates_client.get_earnings_estimates(ticker)
        return {
            "ticker": ticker.upper(),
            "finnhub_configured": True,
            "count": len(estimates) if estimates else 0,
            "estimates": estimates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticker}/debug")
async def debug_polygon(ticker: str):
    """Debug endpoint to see raw Polygon data"""
    try:
        import requests
        api_key = os.getenv("POLYGON_API_KEY", "")
        
        # Get ticker details
        details_url = f"https://api.polygon.io/v3/reference/tickers/{ticker.upper()}?apiKey={api_key}"
        details_resp = requests.get(details_url, timeout=10)
        details = details_resp.json() if details_resp.ok else {"error": details_resp.text}
        
        # Get financials
        financials_url = f"https://api.polygon.io/vX/reference/financials?ticker={ticker.upper()}&timeframe=quarterly&limit=4&apiKey={api_key}"
        fin_resp = requests.get(financials_url, timeout=10)
        financials = fin_resp.json() if fin_resp.ok else {"error": fin_resp.text}
        
        return {
            "ticker": ticker.upper(),
            "details": details,
            "financials": financials
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{ticker}/earnings")
async def get_earnings(ticker: str, db: Session = Depends(get_db)):
    """Get earnings data for a ticker"""
    try:
        data = stock_data_client.get_stock_data(ticker, db)
        return {"ticker": ticker, "earnings": data["earnings"]}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch earnings for {ticker}: {str(e)}")

@router.get("/{ticker}/prices")
async def get_price_history(ticker: str, days: int = 365):
    """Get daily price history for a ticker"""
    try:
        # Use mock data if not using real data
        if stock_data_client._use_mock():
            price_history = stock_data_client.mock.get_price_history(ticker, days=days)
        else:
            price_history = polygon_client._get_price_history(ticker, days=days)
        
        return {
            "ticker": ticker.upper(),
            "days": days,
            "count": len(price_history),
            "prices": price_history
        }
    except Exception as e:
        # Fall back to mock data on error
        price_history = stock_data_client.mock.get_price_history(ticker, days=days)
        return {
            "ticker": ticker.upper(),
            "days": days,
            "count": len(price_history),
            "prices": price_history,
            "_mock": True
        }

@router.get("/{ticker}")
async def get_stock(ticker: str, refresh: bool = False, db: Session = Depends(get_db)):
    """Get stock data including earnings and summary"""
    try:
        data = stock_data_client.get_stock_data(ticker, db, force_refresh=refresh)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not fetch data for {ticker}: {str(e)}")
