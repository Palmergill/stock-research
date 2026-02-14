import React, { useState } from 'react';
import { SearchBar } from './components/SearchBar';
import { MetricCard } from './components/MetricCard';
import { EarningsChart } from './components/EarningsChart';
import { PEChart } from './components/PEChart';
import { RevenueChart } from './components/RevenueChart';
import { FreeCashFlowChart } from './components/FreeCashFlowChart';
import { getStockData } from './services/api';
import { StockResponse } from './types/stock';

function App() {
  const [stockData, setStockData] = useState<StockResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (ticker: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getStockData(ticker);
      setStockData(data);
    } catch (err) {
      setError(`Could not load data for ${ticker}. Please check the ticker symbol.`);
      setStockData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <h1 style={styles.title}>🦞 Stock Research</h1>
        <SearchBar onSearch={handleSearch} loading={loading} />
      </header>

      <main style={styles.main}>
        {error && (
          <div style={styles.error}>{error}</div>
        )}

        {stockData && (
          <>
            <MetricCard summary={stockData.summary} />
            <EarningsChart earnings={stockData.earnings} />
            <RevenueChart earnings={stockData.earnings} />
            <FreeCashFlowChart earnings={stockData.earnings} />
            <PEChart earnings={stockData.earnings} currentPE={stockData.summary.pe_ratio} />
          </>
        )}

        {!stockData && !error && !loading && (
          <div style={styles.empty}>
            <p>Enter a stock ticker to see earnings data and trends.</p>
            <p style={styles.examples}>Try: AAPL, MSFT, GOOGL, NVDA</p>
          </div>
        )}
      </main>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  app: {
    minHeight: '100vh',
    maxWidth: '900px',
    margin: '0 auto',
    padding: '40px 20px',
  },
  header: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '24px',
    marginBottom: '40px',
  },
  title: {
    fontSize: '32px',
    fontWeight: 700,
    background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  },
  main: {
    width: '100%',
  },
  error: {
    background: '#7f1d1d',
    color: '#fecaca',
    padding: '16px 20px',
    borderRadius: '8px',
    marginBottom: '24px',
  },
  empty: {
    textAlign: 'center',
    color: '#64748b',
    padding: '60px 20px',
  },
  examples: {
    marginTop: '12px',
    color: '#94a3b8',
  },
};

export default App;
