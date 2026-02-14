import React from 'react';
import { StockSummaryData } from '../types/stock';

interface MetricCardProps {
  summary: StockSummaryData;
}

const formatMarketCap = (value: number | null): string => {
  if (!value) return 'N/A';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
};

export const MetricCard: React.FC<MetricCardProps> = ({ summary }) => {
  return (
    <div style={styles.container}>
      <h2 style={styles.name}>{summary.name}</h2>
      <p style={styles.ticker}>{summary.ticker}</p>
      
      <div style={styles.grid}>
        <div style={styles.metric}>
          <span style={styles.label}>Market Cap</span>
          <span style={styles.value}>{formatMarketCap(summary.market_cap)}</span>
        </div>
        <div style={styles.metric}>
          <span style={styles.label}>P/E Ratio</span>
          <span style={styles.value}>{summary.pe_ratio?.toFixed(2) || 'N/A'}</span>
        </div>
        <div style={styles.metric}>
          <span style={styles.label}>Next Earnings</span>
          <span style={styles.value}>
            {summary.next_earnings_date 
              ? new Date(summary.next_earnings_date).toLocaleDateString()
              : 'N/A'}
          </span>
        </div>
      </div>
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: '#1e293b',
    borderRadius: '12px',
    padding: '24px',
    marginBottom: '24px',
  },
  name: {
    fontSize: '24px',
    fontWeight: 700,
    color: '#e2e8f0',
    marginBottom: '4px',
  },
  ticker: {
    fontSize: '14px',
    color: '#94a3b8',
    marginBottom: '20px',
    textTransform: 'uppercase',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: '20px',
  },
  metric: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  label: {
    fontSize: '12px',
    color: '#94a3b8',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  value: {
    fontSize: '20px',
    fontWeight: 600,
    color: '#e2e8f0',
  },
};
