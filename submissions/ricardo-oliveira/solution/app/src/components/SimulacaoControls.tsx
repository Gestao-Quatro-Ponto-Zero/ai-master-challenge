"use client";

import { useState, useTransition } from "react";
import { avancarDia, resetarDemo, dispararMensagens, ligarJobDiario } from "@/lib/actions";

// Os controles mexem na planilha de todo mundo que está olhando a demo. Por isso pedem a senha de administração (no README).
export function SimulacaoControls({ live, triggerLigado }: { live: boolean; triggerLigado?: boolean }) {
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<string | null>(null);
  const [senha, setSenha] = useState("");
  const run = (fn: () => Promise<{ error?: string; ok?: string } | undefined>) =>
    start(async () => { const r = await fn(); setMsg(r?.error ? `Erro: ${r.error}` : r?.ok ?? "ok"); });
  const ok = senha.trim().length > 0;
  return (
    <div className="card p-4 space-y-3">
      <label className="block text-sm font-semibold">
        Senha de administração da demo
        <input type="password" value={senha} onChange={(e) => setSenha(e.target.value)} placeholder="está no README da submissão" className="mt-1 w-full md:w-80 border border-line rounded-lg px-3 py-2 bg-white font-normal" />
      </label>
      <p className="text-xs text-grey">Estes botões mudam a planilha pra todo mundo que está olhando a demo (o relógio, as atividades, a fila). Por isso a senha.</p>
      <div className="flex flex-wrap gap-2">
        <button className="btn-primary" disabled={pending || !live || !ok} onClick={() => run(() => avancarDia(senha))}>Avançar um dia</button>
        <button className="btn-secondary" disabled={pending || !live || !ok} onClick={() => run(() => dispararMensagens(senha))}>Mandar as mensagens de hoje</button>
        <button className="btn-secondary" disabled={pending || !live || !ok} onClick={() => run(() => ligarJobDiario(!triggerLigado, senha))}>{triggerLigado ? "Desligar o job diário das 9h" : "Ligar o job diário das 9h"}</button>
        <button className="btn-ghost" disabled={pending || (live && !ok)} onClick={() => run(() => resetarDemo(senha))}>Zerar a demo</button>
      </div>
      {live && <p className="text-xs text-grey">Job diário das 9h: {triggerLigado ? "ligado (o relógio anda sozinho todo dia)" : "desligado durante a avaliação, pra que o \"hoje\" da demo fique parado e bata com o README"}.</p>}
      {!live && <p className="text-xs text-warn">Sem a planilha conectada (APPS_SCRIPT_URL), o relógio não anda. Zerar a demo limpa o que você marcou neste navegador.</p>}
      {msg && <p className="text-sm">{msg}</p>}
    </div>
  );
}
