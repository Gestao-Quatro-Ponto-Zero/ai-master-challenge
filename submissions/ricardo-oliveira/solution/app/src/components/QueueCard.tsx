"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { registrarConta } from "@/lib/actions";
import type { Row } from "@/lib/types";
import { F } from "@/lib/types";
import { str, usd, dateBR } from "@/lib/parse";

export function QueueCard({ row, contas, pos }: { row: Row; contas: string[]; pos: number }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [conta, setConta] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const id = str(row[F.id]);
  const vivo = str(row[F.vivo]);
  const escalada = str(row[F.escalada]);
  const send = () => start(async () => {
    const r = await registrarConta(id, conta);
    setMsg(r?.error ? `Erro: ${r.error}` : r?.ok ?? "ok");
    if (!r?.error) setTimeout(() => router.refresh(), 2500);
  });
  return (
    <article className="card p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-2xl font-extrabold text-gold-dark">{pos}</span>
            <h3 className="text-base font-extrabold">Sem conta no CRM</h3>
            <span className="tag tag-navy">{str(row[F.produto])}</span>
            <span className="font-semibold">{usd(row[F.preco])}</span>
          </div>
          <div className="mt-1 flex gap-2 flex-wrap text-xs">
            <span className={`tag ${vivo === "Vivo" ? "tag-ok" : vivo === "Sem data" ? "tag-navy" : "tag-bad"}`}>{vivo}</span>
            <span className="tag tag-navy">{str(row[F.estagio])}{row[F.diasAberto] ? ` · aberto há ${str(row[F.diasAberto])} dias` : ""}</span>
            <span className={`tag ${escalada === "Escalar pro manager" ? "tag-bad" : "tag-gold"}`}>prazo {dateBR(row[F.prazo])}{escalada === "Escalar pro manager" ? " · vencido" : ""}</span>
          </div>
        </div>
        <div className="text-xs text-grey text-right">{id}</div>
      </div>
      <p className="mt-3 text-sm"><span className="font-semibold">Por quê.</span> O deal existe, mas o CRM não diz de que conta é. Sem conta não dá pra comparar com o ICP nem saber se é hora de recompra.</p>
      <p className="mt-1 text-sm"><span className="font-semibold">Próxima ação.</span> Descobrir a conta deste deal e registrar aqui. Identificada, ele entra na lista pelas regras (vivo fica com você; antigo vai pro dono da conta).</p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <input list="contas" value={conta} onChange={(e) => setConta(e.target.value)} placeholder="nome da conta" className="border border-line rounded-lg px-3 py-2 w-64" />
        <datalist id="contas">{contas.map((c) => <option key={c} value={c} />)}</datalist>
        <button className="btn-primary" disabled={pending || !conta.trim()} onClick={send}>Conta identificada</button>
        {msg && <span className="text-xs text-grey">{msg}</span>}
      </div>
    </article>
  );
}
