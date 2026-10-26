"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { escolherUsuario, limparUsuario, currentUser } from "./session";
import { findUser, isLive, apiPost } from "./data";
import { writeLocalActivity, clearLocalActivities } from "./localActivities";

export type ActionState = { error?: string; ok?: string } | undefined;

export async function escolher(formData: FormData): Promise<void> {
  const key = String(formData.get("quem") || "").trim();
  const user = await findUser(key);
  if (!user) redirect("/");
  await escolherUsuario(key);
  redirect(user.papel === "manager" ? "/manager" : "/meu-dia");
}

export async function trocar(): Promise<void> {
  await limparUsuario();
  redirect("/");
}

export type Acao = "feito" | "ganho" | "perdido" | "separado";

export async function registrar(deal: string, acao: Acao, valor?: number, nota?: string): Promise<ActionState> {
  const user = await currentUser();
  if (!user) return { error: "Sessão expirada." };
  if (isLive()) {
    const r = await apiPost<{ ok?: boolean; error?: string }>({ action: "activity", deal, rep: user.nome, acao, valor: valor ?? 0, nota: nota ?? "" });
    if (r.error) return { error: r.error };
  } else {
    await writeLocalActivity(deal, { acao, valor });
  }
  revalidatePath("/meu-dia");
  revalidatePath("/manager");
  return { ok: `${deal}: ${acao}` };
}

export async function registrarConta(deal: string, conta: string): Promise<ActionState> {
  const user = await currentUser();
  if (!user) return { error: "Sessão expirada." };
  if (!conta.trim()) return { error: "Escreva o nome da conta." };
  if (isLive()) {
    const r = await apiPost<{ ok?: boolean; error?: string; status?: string; conta?: string }>({ action: "conta", deal, rep: user.nome, conta: conta.trim() });
    if (r.error) return { error: r.error };
    await writeLocalActivity(deal, { acao: "conta", conta: r.conta });
    revalidatePath("/meu-dia"); revalidatePath("/fila"); revalidatePath("/manager");
    return { ok: r.status === "Identificada" ? `${r.conta}: identificada. O deal entra na lista pelas regras.` : `${r.conta} não é nenhuma das 85 contas: fica marcado como new logo.` };
  }
  await writeLocalActivity(deal, { acao: "conta", conta: conta.trim() });
  revalidatePath("/meu-dia"); revalidatePath("/fila");
  return { ok: `${conta.trim()}: anotado neste navegador (modo snapshot).` };
}

// Recompra sem deal: o vendedor abriu o deal (ou ligou). A chave é "Conta|Produto", porque ainda não existe deal no CRM.
export async function registrarRecompra(conta: string, produto: string): Promise<ActionState> {
  const user = await currentUser();
  if (!user) return { error: "Sessão expirada." };
  const key = `${conta}|${produto}`;
  if (isLive()) {
    const r = await apiPost<{ ok?: boolean; error?: string }>({ action: "activity", deal: key, rep: user.nome, acao: "recompra", nota: "deal aberto / ligação feita" });
    if (r.error) return { error: r.error };
  } else {
    await writeLocalActivity(key, { acao: "recompra" });
  }
  revalidatePath("/meu-dia");
  return { ok: `${conta} · ${produto}: feito. Vai pro fim do bloco e volta amanhã se continuar sem deal.` };
}

// Controles da demo (relógio, mensagens, zerar) mexem na planilha de todo mundo que está olhando.
// Por isso pedem a senha de administração da demo (DEMO_ADMIN_PASSWORD no Vercel; está no README).
function adminOk(senha: string | undefined): boolean {
  const esperada = process.env.DEMO_ADMIN_PASSWORD?.trim();
  return !!esperada && (senha ?? "").trim() === esperada;
}
const semSenha: ActionState = { error: "Senha de administração da demo incorreta. Está no README da submissão." };

export async function avancarDia(senha?: string): Promise<ActionState> {
  const user = await currentUser();
  if (!user) return { error: "Sessão expirada." };
  if (!adminOk(senha)) return semSenha;
  if (!isLive()) return { error: "Avançar o dia precisa da planilha conectada (APPS_SCRIPT_URL). No snapshot o relógio é fixo." };
  const r = await apiPost<{ ok?: boolean; error?: string; hoje?: string }>({ action: "advance" });
  if (r.error) return { error: r.error };
  revalidatePath("/", "layout");
  return { ok: `Hoje agora é ${r.hoje}` };
}

export async function resetarDemo(senha?: string): Promise<ActionState> {
  const user = await currentUser();
  if (!user) return { error: "Sessão expirada." };
  if (isLive()) {
    if (!adminOk(senha)) return semSenha;
    const r = await apiPost<{ ok?: boolean; error?: string }>({ action: "reset" });
    if (r.error) return { error: r.error };
  } else {
    await clearLocalActivities();
  }
  revalidatePath("/", "layout");
  return { ok: "Demo zerada: relógio em 0 e atividades limpas." };
}

export async function dispararMensagens(senha?: string): Promise<ActionState> {
  const user = await currentUser();
  if (!user) return { error: "Sessão expirada." };
  if (!adminOk(senha)) return semSenha;
  if (!isLive()) return { error: "As mensagens saem do Apps Script; precisa da planilha conectada." };
  const r = await apiPost<{ ok?: boolean; error?: string; mensagens?: number }>({ action: "notify" });
  if (r.error) return { error: r.error };
  return { ok: `${r.mensagens} mensagens enviadas.` };
}

export async function ligarJobDiario(on: boolean, senha?: string): Promise<ActionState> {
  const user = await currentUser();
  if (!user) return { error: "Sessão expirada." };
  if (!adminOk(senha)) return semSenha;
  if (!isLive()) return { error: "O job diário mora no Apps Script; precisa da planilha conectada." };
  const r = await apiPost<{ ok?: boolean; error?: string; triggerLigado?: boolean }>({ action: "trigger", on });
  if (r.error) return { error: r.error };
  revalidatePath("/simulacao");
  return { ok: r.triggerLigado ? "Job diário ligado: às 9h o relógio anda um dia e as mensagens saem." : "Job diário desligado: o relógio só anda por aqui." };
}
