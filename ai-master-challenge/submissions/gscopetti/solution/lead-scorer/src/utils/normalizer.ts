import type { Account, Product, SalesTeam, PipelineOpportunity } from '@/types';

/**
 * Normalize product names to canonical format
 * Handles variations like "GTXPro" → "GTX Pro"
 */
export function normalizeProductName(name: string): string {
  if (!name) return '';

  // Clean up whitespace
  name = name.trim();

  // Map common variations to canonical names
  const productMap: Record<string, string> = {
    'gtxpro': 'GTX Pro',
    'gtx pro': 'GTX Pro',
    'gtxplusoptions': 'GTX Plus Options',
    'gtxplusbasic': 'GTX Plus Basic',
    'gtx plus basic': 'GTX Plus Basic',
    'gtxpluspro': 'GTX Plus Pro',
    'gtx plus pro': 'GTX Plus Pro',
    'mg special': 'MG Special',
    'mgspecial': 'MG Special',
    'mg advanced': 'MG Advanced',
    'mgadvanced': 'MG Advanced',
    'gtk 500': 'GTK 500',
    'gtk500': 'GTK 500',
    'gtk basic': 'GTK Basic',
    'gtkbasic': 'GTK Basic',
  };

  const normalized = productMap[name.toLowerCase()] || name;
  return normalized;
}

/**
 * Normalize account name (uppercase, trim)
 */
export function normalizeAccountName(name: string | null | undefined): string | undefined {
  if (!name) return undefined;
  return name.trim().toUpperCase();
}

/**
 * Normalize sales agent name
 */
export function normalizeSalesAgent(name: string): string {
  if (!name) return '';
  return name.trim();
}

/**
 * Parse date string to Date object
 * Handles formats: YYYY-MM-DD, MM/DD/YYYY
 */
export function parseDate(dateStr: string | null | undefined): Date | null {
  if (!dateStr) return null;

  try {
    // Try ISO format first (YYYY-MM-DD)
    if (dateStr.includes('-')) {
      const date = new Date(dateStr);
      if (!isNaN(date.getTime())) return date;
    }

    // Try slash format (MM/DD/YYYY)
    if (dateStr.includes('/')) {
      const date = new Date(dateStr);
      if (!isNaN(date.getTime())) return date;
    }

    return null;
  } catch {
    return null;
  }
}

/**
 * Parse numeric value safely
 */
export function parseNumber(value: string | number | null | undefined): number {
  if (value === null || value === undefined || value === '') return 0;
  const num = Number(value);
  return isNaN(num) ? 0 : num;
}

/**
 * Normalize and validate account data
 */
export function normalizeAccount(data: Record<string, any>): Account | null {
  try {
    return {
      account: normalizeAccountName(data.account) || '',
      sector: (data.sector || '').trim(),
      year_established: parseNumber(data.year_established),
      revenue: parseNumber(data.revenue),
      employees: parseNumber(data.employees),
      office_location: (data.office_location || '').trim(),
      subsidiary_of: data.subsidiary_of ? (data.subsidiary_of || '').trim() : undefined,
    };
  } catch {
    return null;
  }
}

/**
 * Normalize and validate product data
 */
export function normalizeProduct(data: Record<string, any>): Product | null {
  try {
    const product = normalizeProductName(data.product);
    if (!product) return null;

    return {
      product,
      series: (data.series || '').trim(),
      sales_price: parseNumber(data.sales_price),
    };
  } catch {
    return null;
  }
}

/**
 * Normalize and validate sales team data
 */
export function normalizeSalesTeamMember(data: Record<string, any>): SalesTeam | null {
  try {
    return {
      sales_agent: normalizeSalesAgent(data.sales_agent) || '',
      manager: normalizeSalesAgent(data.manager) || '',
      regional_office: (data.regional_office || '').trim(),
    };
  } catch {
    return null;
  }
}

/**
 * Normalize and validate pipeline opportunity
 */
export function normalizePipelineOpportunity(
  data: Record<string, any>
): PipelineOpportunity | null {
  try {
    const dealStage = (data.deal_stage || '').trim();
    const validStages = ['Won', 'Lost', 'Engaging', 'Prospecting'];

    if (!validStages.includes(dealStage)) {
      console.warn(`Invalid deal stage: ${dealStage}`);
      return null;
    }

    return {
      opportunity_id: (data.opportunity_id || '').trim(),
      sales_agent: normalizeSalesAgent(data.sales_agent) || '',
      product: normalizeProductName(data.product),
      account: normalizeAccountName(data.account),
      deal_stage: dealStage as any,
      engage_date: parseDate(data.engage_date) || new Date(),
      close_date: parseDate(data.close_date) || undefined,
      close_value: parseNumber(data.close_value),
    };
  } catch {
    return null;
  }
}

/**
 * Validate required columns in CSV data
 */
export function validateColumns(
  data: Record<string, any>[],
  requiredColumns: string[]
): { valid: boolean; missingColumns: string[] } {
  if (data.length === 0) {
    return { valid: false, missingColumns: requiredColumns };
  }

  const firstRow = data[0];
  const missingColumns = requiredColumns.filter((col) => !(col in firstRow));

  return {
    valid: missingColumns.length === 0,
    missingColumns,
  };
}
