import React, { useMemo } from 'react';
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { EarningsData } from '../types/stock';

interface EarningsChartProps {
  earnings: EarningsData[];
}

interface ChartDataPoint {
  date: string;
  period: string;
  reported: number | null;
  estimated: number | null;
  surprise: number | null;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload || !payload.length) return null;
  
  const data = payload[0].payload as ChartDataPoint;
  
  return (
    <div className="recharts-tooltip-wrapper">
      <div style={{
        backgroundColor: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
        padding: '12px',
        color: '#e2e8f0',
        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)'
      }}>
        <div style={{ fontWeight: 600, marginBottom: '8px' }}>{label} ({data.period})</div>
        {payload.map((entry: any, index: number) => (
          <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <div style={{ 
              width: 12, 
              height: 12, 
              backgroundColor: entry.color,
              borderRadius: entry.dataKey === 'reported' ? '2px' : '50%'
            }} />
            <span style={{ color: '#94a3b8' }}>{entry.name}:</span>
            <span style={{ fontWeight: 500 }}>${entry.value?.toFixed(2) || 'N/A'}</span>
          </div>
        ))}
        {data.surprise !== null && (
          <div style={{ 
            marginTop: '8px', 
            paddingTop: '8px', 
            borderTop: '1px solid #334155',
            color: data.surprise >= 0 ? '#22c55e' : '#ef4444',
            fontWeight: 600
          }}>
            Surprise: {data.surprise > 0 ? '+' : ''}{data.surprise.toFixed(2)}%
          </div>
        )}
      </div>
    </div>
  );
};

export const EarningsChart: React.FC<EarningsChartProps> = ({ earnings }) => {
  const { chartData, avgReported, trend } = useMemo(() => {
    const data = [...earnings].reverse().map((e) => ({
      date: e.fiscal_date.slice(0, 7),
      period: e.period,
      reported: e.reported_eps,
      estimated: e.estimated_eps,
      surprise: e.surprise_pct,
    }));
    
    const reportedValues = data.map(d => d.reported).filter((v): v is number => v !== null);
    const avg = reportedValues.reduce((a, b) => a + b, 0) / reportedValues.length;
    
    // Simple trend calculation (first half avg vs second half avg)
    const midPoint = Math.floor(reportedValues.length / 2);
    const firstHalf = reportedValues.slice(0, midPoint);
    const secondHalf = reportedValues.slice(midPoint);
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const secondAvg = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
    const trendValue = ((secondAvg - firstAvg) / Math.abs(firstAvg)) * 100;
    
    return { chartData: data, avgReported: avg, trend: trendValue };
  }, [earnings]);

  const trendText = trend > 5 ? '↑ Growing' : trend < -5 ? '↓ Declining' : '→ Stable';
  const trendColor = trend > 5 ? '#22c55e' : trend < -5 ? '#ef4444' : '#f59e0b';

  return (
    <div className="chart-container">
      <div className="chart-header">
        <h3 className="chart-title">EPS: Actual vs Estimated</h3>
        <span className="chart-subtitle" style={{ color: trendColor }}>
          {trendText} ({trend > 0 ? '+' : ''}{trend.toFixed(1)}%)
        </span>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis 
            dataKey="date" 
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
          />
          <YAxis 
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickFormatter={(v) => `$${v}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ paddingTop: '10px' }} />
          <ReferenceLine 
            y={avgReported} 
            stroke="#64748b" 
            strokeDasharray="5 5" 
            label={{ 
              value: `Avg: $${avgReported.toFixed(2)}`, 
              fill: '#94a3b8', 
              fontSize: 11, 
              position: 'right' 
            }}
          />
          <Bar 
            dataKey="reported" 
            name="Actual EPS" 
            fill="#3b82f6" 
            radius={[4, 4, 0, 0]}
          />
          <Line 
            type="monotone" 
            dataKey="estimated" 
            name="Estimated EPS" 
            stroke="#f59e0b" 
            strokeWidth={3}
            dot={{ fill: '#f59e0b', strokeWidth: 2, r: 5 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
