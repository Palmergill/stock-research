export interface EarningsData {
  fiscal_date: string;
  period: string;
  reported_eps: number | null;
  estimated_eps: number | null;
  surprise_pct: number | null;
  revenue: number | null;
  free_cash_flow: number | null;
  pe_ratio: number | null;
}

export interface StockSummaryData {
  ticker: string;
  name: string;
  market_cap: number | null;
  pe_ratio: number | null;
  next_earnings_date: string | null;
}

export interface StockResponse {
  ticker: string;
  name: string;
  earnings: EarningsData[];
  summary: StockSummaryData;
}
