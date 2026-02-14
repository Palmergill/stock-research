import React from 'react';
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
} from 'recharts';
import { EarningsData } from '../types/stock';

interface EarningsChartProps {
  earnings: EarningsData[];
}

export const EarningsChart: React.FC<EarningsChartProps> = ({ earnings }) => {
  // Reverse for chronological order (oldest first for chart)
  const chartData = [...earnings].reverse().map((e) => ({
    period: e.period,
    date: e.fiscal_date.slice(0, 7), // YYYY-MM
    reported: e.reported_eps,
    estimated: e.estimated_eps,
  }));

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>EPS: Actual vs Estimated</h3>
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
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1e293b', 
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#e2e8f0'
            }}
          />
          <Legend />
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
    color: '#e2e8f0',
  },
};
