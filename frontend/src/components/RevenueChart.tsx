// Revenue chart component
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { EarningsData } from '../types/stock';

interface RevenueChartProps {
  earnings: EarningsData[];
}

export const RevenueChart: React.FC<RevenueChartProps> = ({ earnings }) => {
  const chartData = [...earnings].reverse().map((e) => ({
    date: e.fiscal_date.slice(0, 7),
    period: e.period,
    revenue: e.revenue ? e.revenue / 1e9 : 0,
  }));

  const totalRevenue = chartData.reduce((sum, d) => sum + (d.revenue || 0), 0);

  return (
    <div className="chart-container">
      <div className="chart-header">
        <h3 className="chart-title">Revenue by Quarter</h3>
        <span className="chart-subtitle">
          Total (8Q): ${totalRevenue.toFixed(1)}B
        </span>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis 
            dataKey="date" 
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
          />
          <YAxis 
            stroke="#94a3b8"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
            tickFormatter={(value) => `$${value}B`}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1e293b', 
              border: '1px solid #334155',
              borderRadius: '8px',
              color: '#e2e8f0'
            }}
            formatter={(value: number) => [`$${value.toFixed(2)}B`, 'Revenue']}
          />
          <Bar 
            dataKey="revenue" 
            fill="#10b981" 
            radius={[4, 4, 0, 0]}
            name="Revenue"
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
