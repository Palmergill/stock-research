import { useState, useCallback } from 'react';
import { SearchBar } from './components/SearchBar';
import { MetricCard } from './components/MetricCard';
import { EarningsChart } from './components/EarningsChart';
import { PEChart } from './components/PEChart';
import { RevenueChart } from './components/RevenueChart';
import { FreeCashFlowChart } from './components/FreeCashFlowChart';
import { LoadingSkeleton } from './components/LoadingSkeleton';
import { getStockData } from './services/api';
import { StockResponse } from './types/stock';

function App() {
  const [stockData, setStockData] = useState<StockResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastTicker, setLastTicker] = useState<string>('');

  const handleSearch = useCallback(async (ticker: string) => {
    setLoading(true);
    setError(null);
    setLastTicker(ticker);
    
    try {
      const data = await getStockData(ticker);
      setStockData(data);
    } catch (err) {
      setError(`Could not load data for ${ticker}. Please check the ticker symbol and try again.`);
      setStockData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRetry = useCallback(() => {
    if (lastTicker) {
      handleSearch(lastTicker);
    }
  }, [lastTicker, handleSearch]);

  return (
    <div className="app">
      <header className="header">
        <h1 className="title">🦞 Stock Research</h1>
        <SearchBar onSearch={handleSearch} loading={loading} />
      </header>

      <main>
        {error && (
          <div className="error-container">
            <p className="error-message">{error}</p>
            <button className="retry-button" onClick={handleRetry}>
              Try Again
            </button>
          </div>
        )}

        {loading && <LoadingSkeleton />}

        {!loading && stockData && (
          <>
            <MetricCard summary={stockData.summary} earnings={stockData.earnings} />
            <EarningsChart earnings={stockData.earnings} />
            <RevenueChart earnings={stockData.earnings} />
            <FreeCashFlowChart earnings={stockData.earnings} />
            <PEChart earnings={stockData.earnings} currentPE={stockData.summary.pe_ratio} />
          </>
        )}

        {!loading && !stockData && !error && (
          <div className="empty-state">
            <p>Enter a stock ticker to see earnings data and trends.</p>
            <p className="examples">Try: AAPL, MSFT, GOOGL, NVDA, AMZN, META</p>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
