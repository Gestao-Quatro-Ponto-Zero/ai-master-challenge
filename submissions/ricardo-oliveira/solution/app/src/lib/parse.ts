// A planilha fala pt_BR: "18,5" é 18.5. A API devolve números de verdade. Os dois passam aqui.
export function num(v: unknown): number {
  if (typeof v === "number") return v;
  if (v === null || v === undefined || v === "") return 0;
  const s = String(v).trim().replace(/\$/g, "").replace(/\s/g, "");
  // "1.234,5" -> 1234.5 ; "18,5" -> 18.5 ; "275056" -> 275056
  const normalized = s.includes(",") ? s.replace(/\./g, "").replace(",", ".") : s;
  const n = Number(normalized);
  return Number.isFinite(n) ? n : 0;
}
export function str(v: unknown): string {
  if (v === null || v === undefined) return "";
  return String(v);
}
export function bool(v: unknown): boolean {
  return v === true || String(v).toUpperCase() === "TRUE";
}
export function usd(v: unknown): string {
  return "US$ " + Math.round(num(v)).toLocaleString("pt-BR");
}
export function pct(v: unknown): string {
  return (num(v) * 100).toFixed(1).replace(".", ",") + "%";
}
export function dateBR(iso: unknown): string {
  const s = str(iso);
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!m) return s;
  return `${m[3]}/${m[2]}/${m[1]}`;
}
export function weekdayBR(iso: unknown): string {
  const s = str(iso);
  const d = new Date(s + "T12:00:00");
  if (Number.isNaN(d.getTime())) return "";
  return ["domingo", "segunda", "terça", "quarta", "quinta", "sexta", "sábado"][d.getDay()];
}
