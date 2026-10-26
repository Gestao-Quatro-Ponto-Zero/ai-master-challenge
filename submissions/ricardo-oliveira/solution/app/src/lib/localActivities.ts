import "server-only";
import { cookies } from "next/headers";

// Só no modo snapshot: guarda o que o vendedor marcou num cookie, pra demo funcionar sem a planilha.
const NAME = "ls_acts";
export type LocalAct = { acao: "feito" | "ganho" | "perdido" | "separado" | "conta" | "recompra"; valor?: number; conta?: string };

export async function readLocalActivities(): Promise<Record<string, LocalAct>> {
  try {
    const raw = (await cookies()).get(NAME)?.value;
    return raw ? (JSON.parse(raw) as Record<string, LocalAct>) : {};
  } catch { return {}; }
}

export async function writeLocalActivity(deal: string, act: LocalAct): Promise<void> {
  const acts = await readLocalActivities();
  acts[deal] = act;
  (await cookies()).set(NAME, JSON.stringify(acts), { path: "/", httpOnly: true, sameSite: "lax", maxAge: 60 * 60 * 24 * 7 });
}

export async function clearLocalActivities(): Promise<void> {
  (await cookies()).set(NAME, "", { path: "/", maxAge: 0 });
}
