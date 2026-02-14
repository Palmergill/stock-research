import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { EarningsData } from '../types/stock';

interface PEChartProps {
  earnings: EarningsData[];
  currentPE?: number | null;
}

export const PEChart: React.FC<PEChartProps> = ({ earnings, currentPE }) => {
  // Reverse for chronological order (oldest first for chart)
  const chartData = [...earnings].reverse().map((e) => ({
    date: e.fiscal_date.slice(0, 7), // YYYY-MM
    period: e.period,
    pe: e.pe_ratio,
  }));

  // Calculate average P/E for reference line
  const avgPE = chartData.reduce((sum, d) => sum + (d.pe || 0), 0) / chartData.length;

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>P/E Ratio Over Time</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <defs>
            <linearGradient id="peGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis 
            dataKey="date" 
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
          />
          <YAxis 
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            domain={['auto', 'auto']}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1e293b', 
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#e2e8f0'
            }}
            formatter={(value: number) => [value?.toFixed(2), 'P/E Ratio']}
          />
          <ReferenceLine 
            y={avgPE} 
            stroke="#64748b" 
            strokeDasharray="5 5" 
            label={{ value: `Avg: ${avgPE.toFixed(1)}`, fill: '#94a3b8', fontSize: 12, position: 'right' }}
          />
          <Area 
            type="monotone" 
            dataKey="pe" 
            stroke="#8b5cf6" 
            strokeWidth={3}
            fillOpacity={1}
            fill="url(#peGradient)"
            name="P/E Ratio"
          />
        </AreaChart>
      </ResponsiveContainer>
      {currentPE && (
        <div style={styles.currentPE}>
          <span style={styles.label}>Current P/E: </span>
          <span style={styles.value}>{currentPE.toFixed(2)}</span>
          <span style={avgPE > currentPE ? styles.discount : styles.premium}>
            {avgPE > currentPE ? ' (below avg)' : ' (above avg)'}
          </span>
        </div>
      )}
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
  title: {
    marginBottom: '16px',
    fontSize: '18px',
    fontWeight: 600,
    color: '#e2e8f8',
  },
  currentPE: {
    marginTop: '16px',
    paddingTop: '16px',
    borderTop: '1px solid #334155',
    fontSize: '14px',
    color: '#94a3b8',
  },
  label: {
    color: '#64748b',
  },
  value: {
    fontWeight: 600,
    color: '#e2e8f0',
  },
  discount: {
    color: '#22c55e',
    marginLeft: '8px',
  },
  premium: {
    color: '#f59e0b',
    marginLeft: '8px',
  },
};
