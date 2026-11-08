const moneyFmt = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const compactFmt = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 1 });
const pctFmt = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 0 });
const intFmt = new Intl.NumberFormat("pt-BR");
const dateFmt = new Intl.DateTimeFormat("pt-BR", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });
const datetimeFmt = new Intl.DateTimeFormat("pt-BR", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

export const money = (v: number) => moneyFmt.format(v);
export const moneyShort = (v: number) => (Math.abs(v) >= 10_000 ? compactFmt.format(v) : moneyFmt.format(v));
export const pct = (p: number | null | undefined) => (p == null ? "—" : pctFmt.format(p));
export const int = (v: number) => intFmt.format(v);
export const longDate = (iso: string) => dateFmt.format(new Date(iso + "T00:00:00Z"));
export const shortDate = (iso: string | null) => (iso ? iso.split("-").reverse().join("/") : "—");
/** Data+hora curta de um timestamp de decisão (ex: "15 de maio, 09:14"). */
export const shortDateTime = (iso: string) => datetimeFmt.format(new Date(iso));
export const plural = (n: number, one: string, many: string) => `${int(n)} ${n === 1 ? one : many}`;
export const sum = <T,>(xs: T[], f: (x: T) => number) => xs.reduce((acc, x) => acc + f(x), 0);
