import { useMemo } from 'react';
import { StockSummaryData, EarningsData } from '../types/stock';

interface MetricCardProps {
  summary: StockSummaryData;
  earnings: EarningsData[];
}

const formatMarketCap = (value: number | null): string => {
  if (!value) return 'N/A';
  if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
  return `$${value.toLocaleString()}`;
};

const calculateYoYGrowth = (earnings: EarningsData[]): { revenue: number | null; eps: number | null } => {
  if (earnings.length < 4) return { revenue: null, eps: null };
  
  const latest = earnings[0];
  const yearAgo = earnings.find(e => {
    const latestDate = new Date(latest.fiscal_date);
    const eDate = new Date(e.fiscal_date);
    return eDate.getFullYear() === latestDate.getFullYear() - 1 && 
           Math.abs(eDate.getMonth() - latestDate.getMonth()) <= 1;
  });
  
  if (!yearAgo || !latest.revenue || !yearAgo.revenue || !latest.reported_eps || !yearAgo.reported_eps) {
    return { revenue: null, eps: null };
  }
  
  const revenueGrowth = ((latest.revenue - yearAgo.revenue) / yearAgo.revenue) * 100;
  const epsGrowth = ((latest.reported_eps - yearAgo.reported_eps) / Math.abs(yearAgo.reported_eps)) * 100;
  
  return { revenue: revenueGrowth, eps: epsGrowth };
};

const GrowthBadge: React.FC<{ value: number | null; label: string }> = ({ value, label }) => {
  if (value === null) return null;
  
  const isPositive = value >= 0;
  const arrow = isPositive ? '↑' : '↓';
  
  return (
    <div className="metric-item">
      <span className="metric-label">{label} (YoY)</span>
      <span className={`growth-badge ${isPositive ? 'positive' : 'negative'}`}>
        {arrow} {Math.abs(value).toFixed(1)}%
      </span>
    </div>
  );
};

export const MetricCard: React.FC<MetricCardProps> = ({ summary, earnings }) => {
  const growth = useMemo(() => calculateYoYGrowth(earnings), [earnings]);

  return (
    <div className="metric-card">
      <div className="metric-header">
        <h2 className="metric-name">{summary.name}</h2>
        <span className="metric-ticker">{summary.ticker}</span>
      </div>
      
      <div className="metric-grid">
        <div className="metric-item">
          <span className="metric-label">Market Cap</span>
          <span className="metric-value">{formatMarketCap(summary.market_cap)}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">P/E Ratio</span>
          <span className="metric-value">{summary.pe_ratio?.toFixed(2) || 'N/A'}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">Next Earnings</span>
          <span className="metric-value">
            {summary.next_earnings_date 
              ? new Date(summary.next_earnings_date).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  year: 'numeric'
                })
              : 'N/A'}
          </span>
        </div>
        <GrowthBadge value={growth.revenue} label="Revenue" />
        <GrowthBadge value={growth.eps} label="EPS" />
      </div>
    </div>
  );
};
