const MINUS = '−';

export function formatCurrency(amount: number, currency: 'AUD' | 'USD'): string {
  const symbol = currency === 'AUD' ? 'A$' : 'US$';
  const sign = amount < 0 ? MINUS : '';
  const value = Math.abs(amount).toLocaleString('en-AU', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${sign}${symbol}${value}`;
}

export function formatPercent(fraction: number): string {
  const sign = fraction < 0 ? MINUS : '';
  const value = Math.abs(fraction * 100).toFixed(1);
  return `${sign}${value}%`;
}

export function formatDate(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('en-AU', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    timeZone: 'Australia/Sydney',
  });
}
