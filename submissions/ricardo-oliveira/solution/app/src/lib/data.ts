import "server-only";
import type { Config, ManagerData, RepData, RevopsData, Row, User } from "./types";
import { L, F, K, M, R } from "./types";
import { num, str, bool } from "./parse";
import { readLocalActivities } from "./localActivities";

const API = process.env.APPS_SCRIPT_URL?.trim();
const TOKEN = process.env.API_TOKEN?.trim() || "";

export function isLive(): boolean { return !!API; }

async function apiGet<T>(params: Record<string, string>): Promise<T> {
  const url = new URL(API!);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), { cache: "no-store", redirect: "follow" });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return (await res.json()) as T;
}

export async function apiPost<T>(body: Record<string, unknown>): Promise<T> {
  const res = await fetch(API!, {
    method: "POST",
    headers: { "Content-Type": "text/plain;charset=utf-8" }, // Apps Script não aceita preflight
    body: JSON.stringify({ ...body, token: TOKEN }),
    cache: "no-store",
    redirect: "follow",
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return (await res.json()) as T;
}

// ---------- Snapshot (fallback quando a planilha não está conectada) ----------

type Snapshot = {
  geradoEm: string;
  config: Record<string, string>;
  users: User[];
  kpis: Row[];
  lista: Row[];
  fila: Row[];
  manager: { reps: Row[]; managers: Row[] };
  recompra?: Row[];
};

let snapshotCache: Snapshot | null = null;
async function snapshot(): Promise<Snapshot> {
  if (!snapshotCache) {
    const mod = await import("../data/snapshot.json");
    snapshotCache = (mod.default ?? mod) as unknown as Snapshot;
  }
  return snapshotCache;
}

function configFromLabels(c: Record<string, string>): Config {
  const g = (label: string) => c[label] ?? "";
  return {
    fimDosDados: g("Fim dos dados (última data de fechamento)"),
    diasPassados: num(g("Dias passados desde o fim dos dados (N)")),
    hoje: g("Hoje"),
    cicloNormal: num(g("Ciclo normal de quem ganha (mediana, dias)")),
    cicloMaisLongo: num(g("Deal ganho mais longo (dias)")),
    janelaEntrando: num(g("Janela 'entrando na recompra' (dias)")),
    janelaPoucoFora: num(g("Janela 'pouco fora da recompra' (dias)")),
    modoDono: g("Modo de dono"),
    prazoFilaDiasUteis: num(g("Prazo da fila sem conta (dias úteis)")),
    requalificacaoDias: num(g("Requalificação de deal passado do ciclo (dias)")),
    dealsPorSemana: num(g("Deals por vendedor na primeira passada (seg a sex)")),
    ordemDentroDoPasso: g("Ordem dentro do passo"),
    filaPorDia: num(g("Deals sem conta por dia (no Meu dia)")) || 5,
    totais: {
      comConta: num(g("Deals abertos com conta (Lista do Dia)")),
      passo1: num(g("Passo 1: vivo e na hora de recomprar")),
      passo2: num(g("Passo 2: outros vivos")),
      passo3: num(g("Passo 3: antigos, conta na hora de recomprar")),
      passo4: num(g("Passo 4: o resto")),
      semConta: num(g("Deals sem conta (fila)")),
      filaForaDoPrazo: num(g("Fila fora do prazo")),
      confirmar: num(g("Confirmar: a conta comprou de outro vendedor depois de abrir")),
    },
  };
}

// No snapshot, o que o vendedor marcou fica num cookie; aplica o mesmo efeito que a planilha aplicaria.
async function applyLocalActivities(lista: Row[], hoje: string): Promise<Row[]> {
  const acts = await readLocalActivities();
  if (!Object.keys(acts).length) return lista;
  const out: Row[] = [];
  for (const r of lista) {
    const a = acts[str(r[L.id])];
    if (!a) { out.push(r); continue; }
    if (a.acao === "ganho" || a.acao === "perdido") continue; // saiu da lista
    if (a.acao === "conta" || a.acao === "recompra") { out.push(r); continue; }
    // separado: a conta confirmou demanda separada; o deal sai do bloco Confirmar e volta pros passos (aproximação do snapshot)
    const passo = a.acao === "separado" && num(r[L.passo]) === 5 ? (str(r[L.vivo]) === "Vivo" ? 2 : 4) : num(r[L.passo]);
    out.push({ ...r, [L.passo]: passo, [L.separado]: a.acao === "separado" ? true : r[L.separado], [L.ultimoContato]: hoje, [L.feitoHoje]: true, [L.estado]: "aberto" });
  }
  // feito hoje vai pro fim da lista do vendedor, mantendo a ordem relativa
  const byRep = new Map<string, Row[]>();
  out.forEach((r) => {
    const k = str(r[L.trabalha]);
    byRep.set(k, [...(byRep.get(k) ?? []), r]);
  });
  const result: Row[] = [];
  byRep.forEach((rows) => {
    const byOrdem = (a: Row, b: Row) => num(a[L.ordem]) - num(b[L.ordem]);
    const pending = rows.filter((r) => r[L.feitoHoje] !== true).sort(byOrdem);
    const done = rows.filter((r) => r[L.feitoHoje] === true).sort(byOrdem);
    [...pending, ...done].forEach((r, i) => result.push({ ...r, [L.ordem]: i + 1 }));
  });
  return result;
}

// ---------- API pública do módulo ----------

// A lista de vendedores quase não muda; um minuto de cache poupa uma ida à planilha por página.
let usersCache: { at: number; users: User[] } | null = null;
export async function getUsers(): Promise<User[]> {
  if (!API) return (await snapshot()).users;
  if (usersCache && Date.now() - usersCache.at < 60_000) return usersCache.users;
  const users = await apiGet<User[]>({ action: "users" });
  usersCache = { at: Date.now(), users };
  return users;
}

export async function findUser(email: string): Promise<User | null> {
  const e = email.toLowerCase().trim();
  return (await getUsers()).find((u) => u.email.toLowerCase() === e) ?? null;
}

export async function getConfig(): Promise<Config> {
  if (API) return apiGet<Config>({ action: "config" });
  return configFromLabels((await snapshot()).config);
}

export async function getRep(email: string): Promise<RepData | null> {
  if (API) {
    const d = await apiGet<RepData & { error?: string }>({ action: "rep", email });
    if (d.error) return null;
    // Em modo live a planilha é a verdade: a fila esconde só o que já está marcado como identificado lá.
    const fila = d.fila.filter((f) => f["Status (vendedor)"] !== "Identificada");
    return { ...d, fila, recompra: d.recompra ?? [], kpisTime: d.kpisTime ?? [], contas: d.contas ?? [], modo: "live" };
  }
  const s = await snapshot();
  const user = await findUser(email);
  if (!user) return null;
  const config = configFromLabels(s.config);
  const kpi = s.kpis.find((r) => str(r[K.vendedor]) === user.nome) ?? null;
  const listaAll = await applyLocalActivities(s.lista, config.hoje);
  const lista = listaAll
    .filter((r) => str(r[L.trabalha]) === user.nome)
    .sort((a, b) => num(a[L.ordem]) - num(b[L.ordem]));
  const acts = await readLocalActivities();
  const fila = s.fila
    .filter((r) => str(r[F.vendedor]) === user.nome && !acts[str(r[F.id])])
    .sort((a, b) => num(a[F.ordem]) - num(b[F.ordem]));
  const contas = Array.from(new Set(s.lista.map((r) => str(r[L.conta])).filter(Boolean))).sort();
  const recompra = (s.recompra ?? [])
    .filter((r) => str(r[R.dono]) === user.nome && bool(r[R.entra]))
    .map((r) => (acts[`${str(r[R.conta])}|${str(r[R.produto])}`]?.acao === "recompra" ? { ...r, [R.feito]: true } : r))
    .sort((a, b) => (bool(a[R.feito]) === bool(b[R.feito]) ? num(a[R.ordem]) - num(b[R.ordem]) : bool(a[R.feito]) ? 1 : -1));
  const kpisTime = s.kpis.filter((r) => str(r["Manager"]) === user.manager);
  return { user, config, kpi, kpisTime, lista, fila, recompra, contas, modo: "snapshot" };
}

export async function getManager(email: string): Promise<ManagerData | null> {
  if (API) {
    const d = await apiGet<ManagerData & { error?: string }>({ action: "manager", email });
    if (d.error) return null;
    return { ...d, recompra: d.recompra ?? [], kpisTime: d.kpisTime ?? [], modo: "live" };
  }
  const s = await snapshot();
  const user = await findUser(email);
  if (!user) return null;
  const config = configFromLabels(s.config);
  const time = s.manager.reps.filter((r) => str(r[M.manager]) === user.nome);
  const resumo = s.manager.managers.find((r) => str(r["Manager"]) === user.nome) ?? null;
  const nomes = new Set(time.map((r) => str(r[M.vendedor])));
  const listaAll = await applyLocalActivities(s.lista, config.hoje);
  const lista = listaAll.filter((r) => nomes.has(str(r[L.trabalha])));
  const fila = s.fila.filter((r) => nomes.has(str(r[F.vendedor])));
  const recompra = (s.recompra ?? []).filter((r) => nomes.has(str(r[R.dono])) && bool(r[R.entra]));
  const kpisTime = s.kpis.filter((r) => str(r["Manager"]) === user.nome);
  return { user, config, time, resumo, kpisTime, lista, fila, recompra, modo: "snapshot" };
}

export async function getRevops(): Promise<RevopsData> {
  if (API) {
    const d = await apiGet<RevopsData>({ action: "revops" });
    return { ...d, recompra: d.recompra ?? [], kpis: d.kpis ?? [], modo: "live" };
  }
  const s = await snapshot();
  return { config: configFromLabels(s.config), reps: s.manager.reps, managers: s.manager.managers, recompra: s.recompra ?? [], kpis: s.kpis, modo: "snapshot" };
}
