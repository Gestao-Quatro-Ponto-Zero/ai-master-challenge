import fs from "fs";
import path from "path";

export interface CalendarEntry {
  id: string;
  generated_at: string;
  status: "pendente" | "aprovado" | "publicado";
  scheduled_date: string;
  scheduled_time: string;
  platform: string;
  niche: string;
  audience: string;
  script: {
    title: string;
    copy: string;
    visual_spec: string;
    hashtags: string[];
    cta: string;
    thumbnail_description: string;
    publish_time: string;
  };
  scores: {
    originality: number;
    feasibility: number;
    alignment: number;
    overall: number;
  };
  approved_by: string | null;
  approved_at: string | null;
}

interface CalendarData {
  entries: CalendarEntry[];
}

const CALENDAR_PATH = path.join(process.cwd(), "public", "data", "calendar.json");
const HISTORY_PATH = path.join(process.cwd(), "public", "data", "content-history.json");

// ============================================================
// HISTORICO — guarda conteudos descartados e reprovados por nota
// A IA usa esse historico como referencia do que NAO funciona
// ============================================================

export interface HistoryEntry {
  id: string;
  reason: "descartado_gestor" | "nota_baixa";
  original: CalendarEntry;
  discarded_at: string;
  scores: CalendarEntry["scores"];
}

interface HistoryData {
  entries: HistoryEntry[];
}

export function readHistory(): HistoryData {
  try {
    const raw = fs.readFileSync(HISTORY_PATH, "utf-8");
    return JSON.parse(raw);
  } catch {
    return { entries: [] };
  }
}

function writeHistory(data: HistoryData): void {
  fs.writeFileSync(HISTORY_PATH, JSON.stringify(data, null, 2), "utf-8");
}

export function addToHistory(entry: CalendarEntry, reason: HistoryEntry["reason"]): void {
  const history = readHistory();
  history.entries.push({
    id: entry.id,
    reason,
    original: entry,
    discarded_at: new Date().toISOString(),
    scores: entry.scores,
  });
  writeHistory(history);
}

/**
 * Retorna resumo do historico para alimentar o prompt da IA
 * Formato: lista de titulos + motivo + score para a IA aprender
 */
export function getHistorySummaryForPrompt(limit = 20): string {
  const history = readHistory();
  if (history.entries.length === 0) return "Nenhum conteudo descartado anteriormente.";

  const recent = history.entries.slice(-limit);
  const lines = recent.map((h) => {
    const label = h.reason === "descartado_gestor" ? "DESCARTADO pelo gestor" : `REPROVADO (nota ${h.scores.overall})`;
    return `- "${h.original.script.title}" (${h.original.platform}/${h.original.niche}) — ${label}`;
  });

  return `Conteudos anteriores que NAO funcionaram (evite ideias similares):\n${lines.join("\n")}`;
}

export function readCalendar(): CalendarData {
  try {
    const raw = fs.readFileSync(CALENDAR_PATH, "utf-8");
    return JSON.parse(raw);
  } catch {
    return { entries: [] };
  }
}

export function writeCalendar(data: CalendarData): void {
  fs.writeFileSync(CALENDAR_PATH, JSON.stringify(data, null, 2), "utf-8");
}

export function addEntries(entries: CalendarEntry[]): void {
  const cal = readCalendar();
  cal.entries.push(...entries);
  writeCalendar(cal);
}

export function updateEntryStatus(
  id: string,
  status: CalendarEntry["status"],
  extra?: Partial<CalendarEntry>
): CalendarEntry | null {
  const cal = readCalendar();
  const entry = cal.entries.find((e) => e.id === id);
  if (!entry) return null;
  entry.status = status;
  if (extra) Object.assign(entry, extra);
  writeCalendar(cal);
  return entry;
}

export function removeEntry(id: string): boolean {
  const cal = readCalendar();
  const entry = cal.entries.find((e) => e.id === id);
  if (!entry) return false;

  // Salvar no historico antes de remover
  addToHistory(entry, "descartado_gestor");

  cal.entries = cal.entries.filter((e) => e.id !== id);
  writeCalendar(cal);
  return true;
}

export function rescheduleEntry(
  id: string,
  date: string,
  time: string
): CalendarEntry | null {
  const cal = readCalendar();
  const entry = cal.entries.find((e) => e.id === id);
  if (!entry) return null;
  entry.scheduled_date = date;
  entry.scheduled_time = time;
  writeCalendar(cal);
  return entry;
}
