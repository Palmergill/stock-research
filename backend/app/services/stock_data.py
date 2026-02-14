# Popular stocks for search suggestions
POPULAR_STOCKS = {
    "AAPL": {"name": "Apple Inc.", "sector": "Technology"},
    "MSFT": {"name": "Microsoft Corporation", "sector": "Technology"},
    "GOOGL": {"name": "Alphabet Inc.", "sector": "Technology"},
    "AMZN": {"name": "Amazon.com Inc.", "sector": "Consumer Discretionary"},
    "NVDA": {"name": "NVIDIA Corporation", "sector": "Technology"},
    "TSLA": {"name": "Tesla Inc.", "sector": "Consumer Discretionary"},
    "META": {"name": "Meta Platforms Inc.", "sector": "Technology"},
    "NFLX": {"name": "Netflix Inc.", "sector": "Communication Services"},
    "JPM": {"name": "JPMorgan Chase & Co.", "sector": "Financials"},
    "V": {"name": "Visa Inc.", "sector": "Financials"},
    "JNJ": {"name": "Johnson & Johnson", "sector": "Healthcare"},
    "WMT": {"name": "Walmart Inc.", "sector": "Consumer Staples"},
    "PG": {"name": "Procter & Gamble Co.", "sector": "Consumer Staples"},
    "DIS": {"name": "Walt Disney Co.", "sector": "Communication Services"},
    "MA": {"name": "Mastercard Inc.", "sector": "Financials"},
    "HD": {"name": "Home Depot Inc.", "sector": "Consumer Discretionary"},
    "BAC": {"name": "Bank of America Corp.", "sector": "Financials"},
    "ABBV": {"name": "AbbVie Inc.", "sector": "Healthcare"},
    "PFE": {"name": "Pfizer Inc.", "sector": "Healthcare"},
    "KO": {"name": "Coca-Cola Co.", "sector": "Consumer Staples"},
    "PEP": {"name": "PepsiCo Inc.", "sector": "Consumer Staples"},
    "MRK": {"name": "Merck & Co.", "sector": "Healthcare"},
    "CSCO": {"name": "Cisco Systems Inc.", "sector": "Technology"},
    "TMO": {"name": "Thermo Fisher Scientific Inc.", "sector": "Healthcare"},
    "ACN": {"name": "Accenture plc", "sector": "Technology"},
    "ADBE": {"name": "Adobe Inc.", "sector": "Technology"},
    "CRM": {"name": "Salesforce Inc.", "sector": "Technology"},
    "NKE": {"name": "Nike Inc.", "sector": "Consumer Discretionary"},
    "ABT": {"name": "Abbott Laboratories", "sector": "Healthcare"},
    "CMCSA": {"name": "Comcast Corporation", "sector": "Communication Services"},
    "XOM": {"name": "Exxon Mobil Corporation", "sector": "Energy"},
    "CVX": {"name": "Chevron Corporation", "sector": "Energy"},
    "LLY": {"name": "Eli Lilly and Company", "sector": "Healthcare"},
    "AVGO": {"name": "Broadcom Inc.", "sector": "Technology"},
    "TXN": {"name": "Texas Instruments Inc.", "sector": "Technology"},
    "COST": {"name": "Costco Wholesale Corporation", "sector": "Consumer Staples"},
    "QCOM": {"name": "Qualcomm Inc.", "sector": "Technology"},
    "NEE": {"name": "NextEra Energy Inc.", "sector": "Utilities"},
    "UPS": {"name": "United Parcel Service Inc.", "sector": "Industrials"},
    "PM": {"name": "Philip Morris International Inc.", "sector": "Consumer Staples"},
    "RTX": {"name": "Raytheon Technologies Corporation", "sector": "Industrials"},
    "HON": {"name": "Honeywell International Inc.", "sector": "Industrials"},
    "UNH": {"name": "UnitedHealth Group Inc.", "sector": "Healthcare"},
    "BMY": {"name": "Bristol Myers Squibb Co.", "sector": "Healthcare"},
    "AMD": {"name": "Advanced Micro Devices Inc.", "sector": "Technology"},
    "INTC": {"name": "Intel Corporation", "sector": "Technology"},
    "SPGI": {"name": "S&P Global Inc.", "sector": "Financials"},
    "IBM": {"name": "International Business Machines", "sector": "Technology"},
    "SBUX": {"name": "Starbucks Corporation", "sector": "Consumer Discretionary"},
    "GS": {"name": "Goldman Sachs Group Inc.", "sector": "Financials"},
    "MS": {"name": "Morgan Stanley", "sector": "Financials"},
    "BLK": {"name": "BlackRock Inc.", "sector": "Financials"},
    "PLTR": {"name": "Palantir Technologies Inc.", "sector": "Technology"},
    "UBER": {"name": "Uber Technologies Inc.", "sector": "Technology"},
    "LYFT": {"name": "Lyft Inc.", "sector": "Technology"},
    "SNOW": {"name": "Snowflake Inc.", "sector": "Technology"},
    "ZM": {"name": "Zoom Video Communications Inc.", "sector": "Technology"},
    "SHOP": {"name": "Shopify Inc.", "sector": "Technology"},
    "SQ": {"name": "Block Inc.", "sector": "Technology"},
    "PYPL": {"name": "PayPal Holdings Inc.", "sector": "Technology"},
    "ROKU": {"name": "Roku Inc.", "sector": "Technology"},
    "TWLO": {"name": "Twilio Inc.", "sector": "Technology"},
    "DDOG": {"name": "Datadog Inc.", "sector": "Technology"},
    "NET": {"name": "Cloudflare Inc.", "sector": "Technology"},
    "CRWD": {"name": "CrowdStrike Holdings Inc.", "sector": "Technology"},
    "OKTA": {"name": "Okta Inc.", "sector": "Technology"},
    "MDB": {"name": "MongoDB Inc.", "sector": "Technology"},
}

def search_stocks(query: str, limit: int = 10) -> list:
    """Search stocks by ticker or company name"""
    if not query:
        return []
    
    query = query.upper().strip()
    results = []
    
    for ticker, info in POPULAR_STOCKS.items():
        ticker_upper = ticker.upper()
        name_upper = info["name"].upper()
        
        # Check if query matches ticker or name
        if query in ticker_upper or query in name_upper:
            results.append({
                "ticker": ticker,
                "name": info["name"],
                "sector": info["sector"]
            })
        
        if len(results) >= limit:
            break
    
    # Sort by relevance (exact ticker match first)
    results.sort(key=lambda x: (
        0 if x["ticker"].upper() == query else 1,
        0 if x["ticker"].upper().startswith(query) else 1,
        x["ticker"]
    ))
    
    return results[:limit]
