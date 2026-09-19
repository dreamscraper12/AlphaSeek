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
  currency: 'AUD' | 'USD';
  note_slug: string | null;
}

export interface ClosedPosition {
  instrument_id: string;
  type: 'equity' | 'etf' | 'option' | 'crypto';
  realised_pnl: number;
  note_slug: string | null;
}

export interface Contribution {
  date: string;
  instrument_id: string;
  contribution: number;
}

export interface PeriodReturns {
  '1M': number | null;
  '3M': number | null;
  YTD: number | null;
  '1Y': number | null;
  since_inception: number | null;
}

export interface Drawdown {
  peak_date: string;
  trough_date: string;
  drawdown: number;
}

export interface SideMetrics {
  returns: PeriodReturns;
  annualised_return: number | null;
  annualised_volatility: number | null;
  max_drawdown: Drawdown | null;
  current_drawdown: number | null;
}

export interface PortfolioMetrics extends SideMetrics {
  beta: number | null;
  correlation: number | null;
  excess_return: number | null;
}

export interface Metrics {
  portfolio: PortfolioMetrics | null;
  benchmark: SideMetrics | null;
}

export interface Status {
  last_valuation_date: string | null;
  inception_date: string | null;
  inception_deposit: number | null;
  stale_prices: string[];
  warnings: string[];
  cash_by_currency: Record<string, number>;
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

export function getClosedPositions(): ClosedPosition[] {
  return closedPositions as ClosedPosition[];
}

export function getTrades(): Trade[] {
  return trades as Trade[];
}

export function getMetrics(): Metrics {
  return metrics as Metrics;
}

export function getAttribution(): Contribution[] {
  return attribution as Contribution[];
}
