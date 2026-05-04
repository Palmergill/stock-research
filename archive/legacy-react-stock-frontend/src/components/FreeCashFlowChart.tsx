// Free cash flow chart component
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { EarningsData } from '../types/stock';

interface FreeCashFlowChartProps {
  earnings: EarningsData[];
}

export const FreeCashFlowChart: React.FC<FreeCashFlowChartProps> = ({ earnings }) => {
  const chartData = [...earnings].reverse().map((e) => ({
    date: e.fiscal_date.slice(0, 7),
    period: e.period,
    revenue: e.revenue ? e.revenue / 1e9 : 0,
    fcf: e.free_cash_flow ? e.free_cash_flow / 1e9 : 0,
    fcfMargin: e.revenue && e.free_cash_flow 
      ? (e.free_cash_flow / e.revenue) * 100 
      : 0,
  }));

  const avgMargin = chartData.reduce((sum, d) => sum + d.fcfMargin, 0) / chartData.length;

  return (
    <div className="chart-container">
      <div className="chart-header">
        <h3 className="chart-title">Free Cash Flow</h3>
        <span className="chart-subtitle">
          Avg Margin: {avgMargin.toFixed(1)}%
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
            yAxisId="left"
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickFormatter={(value) => `$${value}B`}
          />
          <YAxis 
            yAxisId="right"
            orientation="right"
            stroke="#f59e0b"
            tick={{ fill: '#f59e0b', fontSize: 12 }}
            tickFormatter={(value) => `${value.toFixed(0)}%`}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1e293b', 
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#e2e8f0'
            }}
            formatter={(value: number, name: string) => {
              if (name === 'FCF Margin') return [`${value.toFixed(1)}%`, name];
              return [`$${value.toFixed(2)}B`, name];
            }}
          />
          <Legend wrapperStyle={{ paddingTop: '10px' }} />
          <Bar 
            yAxisId="left"
            dataKey="fcf" 
            fill="#06b6d4" 
            radius={[4, 4, 0, 0]}
            name="Free Cash Flow"
          />
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="fcfMargin" 
            stroke="#f59e0b" 
            strokeWidth={3}
            dot={{ fill: '#f59e0b', strokeWidth: 2, r: 5 }}
            name="FCF Margin"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
