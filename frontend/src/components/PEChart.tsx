import { useMemo } from 'react';
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
  const { chartData, avgPE, minPE, maxPE } = useMemo(() => {
    const data = [...earnings].reverse().map((e) => ({
      date: e.fiscal_date.slice(0, 7),
      period: e.period,
      pe: e.pe_ratio,
    }));
    
    const peValues = data.map(d => d.pe).filter((v): v is number => v !== null);
    const avg = peValues.reduce((a, b) => a + b, 0) / peValues.length;
    
    return { 
      chartData: data, 
      avgPE: avg,
      minPE: Math.min(...peValues),
      maxPE: Math.max(...peValues)
    };
  }, [earnings]);

  const peContext = currentPE && avgPE 
    ? currentPE > avgPE * 1.1 ? 'Premium' 
    : currentPE < avgPE * 0.9 ? 'Discount' 
    : 'Fair'
    : '';

  return (
    <div className="chart-container">
      <div className="chart-header">
        <h3 className="chart-title">P/E Ratio Over Time</h3>
        <span className="chart-subtitle" style={{ color: '#8b5cf6' }}>
          Range: {minPE.toFixed(1)}x - {maxPE.toFixed(1)}x
        </span>
      </div>
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
            tickFormatter={(v) => `${v}x`}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1e293b', 
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#e2e8f0'
            }}
            formatter={(value: number) => [`${value?.toFixed(2)}x`, 'P/E Ratio']}
          />
          <ReferenceLine 
            y={avgPE} 
            stroke="#64748b" 
            strokeDasharray="5 5" 
            label={{ 
              value: `Avg: ${avgPE.toFixed(1)}x`, 
              fill: '#94a3b8', 
              fontSize: 11, 
              position: 'right' 
            }}
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
        <div style={{ 
          marginTop: '16px', 
          paddingTop: '16px', 
          borderTop: '1px solid #334155',
          fontSize: '14px',
          color: '#94a3b8',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>
            <span style={{ color: '#64748b' }}>Current P/E: </span>
            <span style={{ fontWeight: 600, color: '#e2e8f0' }}>{currentPE.toFixed(2)}x</span>
          </span>
          {peContext && (
            <span style={{ 
              color: peContext === 'Premium' ? '#f59e0b' : peContext === 'Discount' ? '#22c55e' : '#94a3b8',
              fontWeight: 500
            }}>
              {peContext} vs avg
            </span>
          )}
        </div>
      )}
    </div>
  );
};
