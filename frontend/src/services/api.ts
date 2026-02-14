import axios from 'axios';
import { StockResponse } from '../types/stock';

const API_URL = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: API_URL ? `${API_URL}/api` : '/api',
});

export async function getStockData(ticker: string): Promise<StockResponse> {
  const response = await api.get(`/stocks/${ticker}`);
  return response.data;
}
