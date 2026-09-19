import status from '../../data/generated/status.json';
import navDaily from '../../data/generated/nav_daily.json';
import benchmarkDaily from '../../data/generated/benchmark_daily.json';
import holdings from '../../data/generated/holdings.json';
import closedPositions from '../../data/generated/closed_positions.json';
import trades from '../../data/generated/trades.json';
import metrics from '../../data/generated/metrics.json';
import attribution from '../../data/generated/attribution.json';

export interface NavPoint {
  date: string;
  nav: number;
  index: number;
}

export interface Holding {
  instrument_id: string;
  type: 'equity' | 'etf' | 'option' | 'crypto';
  weight: number;
  average_cost: number;
  price: number;
  price_as_of: string;
  return: number;
  contribution: number;
  note_slug: string | null;
}

export interface Trade {
  trade_id: string;
  executed_at: string;
  instrument_id: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  note_slug: string | null;
}

export interface Status {
  last_valuation_date: string | null;
  stale_prices: string[];
  warnings: string[];
}

export function getStatus(): Status {
  return status as Status;
}

export function getNavDaily(): NavPoint[] {
  return navDaily as NavPoint[];
}

export function getBenchmarkDaily(): NavPoint[] {
  return benchmarkDaily as NavPoint[];
}

export function getHoldings(): Holding[] {
  return holdings as Holding[];
}

export function getClosedPositions(): unknown[] {
  return closedPositions as unknown[];
}

export function getTrades(): Trade[] {
  return trades as Trade[];
}

export function getMetrics(): { portfolio: unknown; benchmark: unknown } {
  return metrics as { portfolio: unknown; benchmark: unknown };
}

export function getAttribution(): unknown[] {
  return attribution as unknown[];
}
