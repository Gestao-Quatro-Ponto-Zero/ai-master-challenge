/**
 * Correções de inconsistências encontradas no CRM. Cada entrada aqui
 * corresponde a um item do relatório de qualidade (ver build-dataset.ts).
 */

/** O pipeline usa "GTXPro"; o catálogo de produtos usa "GTX Pro". */
const PRODUCT_ALIASES: Record<string, string> = {
  GTXPro: "GTX Pro",
};

/** O cadastro de contas grafa "technolgy". */
const SECTOR_ALIASES: Record<string, string> = {
  technolgy: "technology",
};

export function normalizeProduct(name: string): string {
  const trimmed = name.trim();
  return PRODUCT_ALIASES[trimmed] ?? trimmed;
}

export function normalizeSector(sector: string): string {
  const key = sector.trim().toLowerCase();
  return SECTOR_ALIASES[key] ?? key;
}

export function isProductAlias(name: string): boolean {
  return name.trim() in PRODUCT_ALIASES;
}

export function isSectorAlias(sector: string): boolean {
  return sector.trim().toLowerCase() in SECTOR_ALIASES;
}
