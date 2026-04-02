export function normalizeProduct(name: string): string {
  return name.replace(/\s+/g, '');
}

export function safeFloat(val: string | undefined | null, fallback = 0): number {
  if (!val || val.trim() === '') return fallback;
  const n = parseFloat(val);
  return isNaN(n) ? fallback : n;
}

export function daysBetween(dateStr: string, refDate: Date): number {
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return 0;
  return Math.max(0, Math.floor((refDate.getTime() - d.getTime()) / (1000 * 60 * 60 * 24)));
}

export const REFERENCE_DATE = new Date('2017-12-27');

export const EXPECTED_HEADERS: Record<string, string[]> = {
  'sales_pipeline.csv': ['opportunity_id', 'sales_agent', 'product', 'account', 'deal_stage', 'engage_date', 'close_date', 'close_value'],
  'sales_teams.csv': ['sales_agent', 'manager', 'regional_office'],
  'products.csv': ['product', 'series', 'sales_price'],
  'accounts.csv': ['account', 'sector', 'year_established', 'revenue', 'employees', 'office_location', 'subsidiary_of'],
  'metadata.csv': ['Table', 'Field', 'Description'],
};

export function displayAccount(account: string): string {
  return account && account.trim() !== '' ? account : 'Conta não identificada';
}

export function formatCurrency(value: number): string {
  if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value.toFixed(0)}`;
}

export function percentile(arr: number[], p: number): number {
  if (arr.length === 0) return 0;
  const sorted = [...arr].sort((a, b) => a - b);
  const idx = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, idx)];
}
