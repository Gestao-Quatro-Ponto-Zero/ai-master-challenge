/** Formatação compartilhada — importada por toda superfície (listagem,
 * tiles, painel de detalhe, rollup) para que os mesmos números nunca
 * divirjam de uma tela para outra (design.md, decisão 9). */

export function formatUsd(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "USD" });
}

export function formatPct(value: number, casas = 1): string {
  return `${(value * 100).toFixed(casas)}%`;
}

export function formatIdade(ageDays: number | null): string {
  if (ageDays === null) return "—";
  return `${Math.round(ageDays)}d`;
}

export function formatData(iso: string): string {
  if (!iso) return "—";
  const [ano, mes, dia] = iso.split("-");
  if (!ano || !mes || !dia) return iso;
  return `${dia}/${mes}/${ano}`;
}
