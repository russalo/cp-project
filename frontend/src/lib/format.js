// Shared display formatters. Centralizing so commas / decimals / "—" rendering
// is consistent across every page.

const MONEY_FMT = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

/**
 * Format a money value (string or number) with thousands separators.
 * Returns a plain string — "—" for null/undefined/empty input (or the
 * empty string when {emDash: false}), otherwise the formatted currency
 * string.
 */
export function fmtMoney(value, { emDash = true } = {}) {
  if (value === null || value === undefined || value === '') {
    return emDash ? '—' : ''
  }
  const n = Number(value)
  if (Number.isNaN(n)) return String(value)
  return MONEY_FMT.format(n)
}

/**
 * Format a percentage value stored as a Decimal (0.1500 → "15.00%").
 */
export function fmtPct(value) {
  if (value === null || value === undefined || value === '') return '—'
  const n = Number(value)
  if (Number.isNaN(n)) return String(value)
  return `${(n * 100).toFixed(2)}%`
}

/**
 * Format an hours value — one decimal place, never more.
 */
export function fmtHours(value) {
  if (value === null || value === undefined || value === '') return '—'
  return Number(value).toFixed(1)
}
