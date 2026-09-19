const MINUS = '−';

function sign(value: number, forceSign: boolean): string {
  if (value < 0) return MINUS;
  // Section 16: gains and losses always carry a sign, so the figure reads
  // correctly without relying on colour. An exact zero is neither.
  return forceSign && value > 0 ? '+' : '';
}

function currencySymbol(currency: 'AUD' | 'USD'): string {
  return currency === 'AUD' ? 'A$' : 'US$';
}

function amount(value: number, decimals: number): string {
  return Math.abs(value).toLocaleString('en-AU', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/** Absolute money: prices, balances, per-unit figures. */
export function formatCurrency(value: number, currency: 'AUD' | 'USD'): string {
  return `${sign(value, false)}${currencySymbol(currency)}${amount(value, 2)}`;
}

/** Portfolio-scale money, where cents are noise: the headline, the curve. */
export function formatCurrencyWhole(value: number, currency: 'AUD' | 'USD'): string {
  return `${sign(value, false)}${currencySymbol(currency)}${amount(value, 0)}`;
}

/** Money that represents a gain or loss, so it always carries a sign. */
export function formatSignedCurrency(value: number, currency: 'AUD' | 'USD'): string {
  return `${sign(value, true)}${currencySymbol(currency)}${amount(value, 2)}`;
}

/** A plain proportion, such as a position weight. */
export function formatPercent(fraction: number): string {
  return `${sign(fraction, false)}${Math.abs(fraction * 100).toFixed(1)}%`;
}

/** A return or contribution, so it always carries a sign. */
export function formatSignedPercent(fraction: number): string {
  return `${sign(fraction, true)}${Math.abs(fraction * 100).toFixed(1)}%`;
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
