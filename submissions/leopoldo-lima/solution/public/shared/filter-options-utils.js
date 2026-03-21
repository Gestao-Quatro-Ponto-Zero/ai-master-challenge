/**
 * Fonte única de normalização / ordenação / deduplicação para listas do filter-options (CRP-CBX-05).
 * @param {unknown} raw
 * @returns {string[]}
 */
export function normalizeSortDedupeStrings(raw) {
  const arr = Array.isArray(raw) ? raw : [];
  const seen = new Set();
  const out = [];
  for (const item of arr) {
    const s = String(item ?? "").trim();
    if (!s) continue;
    const key = s.toLocaleLowerCase("pt-BR");
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(s);
  }
  out.sort((a, b) => a.localeCompare(b, "pt-BR", { sensitivity: "base" }));
  return out;
}

/**
 * Filtra lista de gestores já normalizada: case-insensitive, prefixo primeiro, depois "contém".
 * @param {string[]} managers
 * @param {string} query
 * @param {{ minLen?: number }} [opts]
 * @returns {string[]}
 */
export function filterManagersByQuery(managers, query, opts = {}) {
  const minLen = opts.minLen ?? 3;
  const t = String(query ?? "").trim();
  if (t.length < minLen) return [];
  const tn = t.toLocaleLowerCase("pt-BR");
  /** @type {string[]} */
  const prefix = [];
  /** @type {string[]} */
  const contains = [];
  const seen = new Set();
  for (const m of managers) {
    const s = String(m ?? "").trim();
    if (!s) continue;
    const ln = s.toLocaleLowerCase("pt-BR");
    if (!ln.includes(tn)) continue;
    const key = ln;
    if (seen.has(key)) continue;
    seen.add(key);
    if (ln.startsWith(tn)) prefix.push(s);
    else contains.push(s);
  }
  const cmp = (a, b) => a.localeCompare(b, "pt-BR", { sensitivity: "base" });
  prefix.sort(cmp);
  contains.sort(cmp);
  return [...prefix, ...contains];
}

/**
 * Lista completa (query vazia) ou filtro incremental com prefixo antes de contém (CRP-FIN-01/02).
 * @param {string[]} managers
 * @param {string} query
 * @returns {string[]}
 */
export function listAllOrFilterManagers(managers, query) {
  const t = String(query ?? "").trim();
  if (!t.length) return managers.slice();
  return filterManagersByQuery(managers, t, { minLen: 1 });
}
