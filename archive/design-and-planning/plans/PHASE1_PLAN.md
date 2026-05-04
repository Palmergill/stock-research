# Phase 1 Implementation Plan

## Goals
1. Remove Yahoo Finance fallback code
2. Implement optimized caching per data type
3. Update database schema for new models
4. Improve Polygon-only error handling

## Step 1: Clean up yfinance_client.py
- Remove Yahoo Finance imports and methods
- Keep the client structure but make it Polygon-only
- Update get_stock_data() to only use Polygon

## Step 2: Update polygon_client.py
- Add TTL awareness (financials 24h, prices 1min, etc.)
- Better error handling with specific Polygon error codes
- Add logging for debugging

## Step 3: Update database schema
- Add new columns to existing tables
- Create migration script
- No new tables yet (those come in Phase 3)

## Step 4: Update caching logic
- Different TTL for different data types in yfinance_client
- Check age before returning cached data

## Step 5: Update API routers
- Remove fallback error messages
- Better Polygon-specific error handling

## Step 6: Testing
- Verify all endpoints work with Polygon only
- Check error handling when Polygon is down
- Verify cache TTLs are respected
