"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { registrarRecompra } from "@/lib/actions";
import type { Row } from "@/lib/types";
import { R } from "@/lib/types";
import { str, usd, bool } from "@/lib/parse";

export function RecompraCard({ row }: { row: Row }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<string | null>(null);
  const situacao = str(row[R.situacao]);
  const feito = bool(row[R.feito]);
  const conta = str(row[R.conta]);
  const produto = str(row[R.produto]);
  const send = () => start(async () => {
    const r = await registrarRecompra(conta, produto);
    setMsg(r?.error ? `Erro: ${r.error}` : r?.ok ?? "ok");
    if (!r?.error) setTimeout(() => router.refresh(), 2500);
  });
  return (
    <article className={`card p-4 border-gold/60 ${feito ? "opacity-60" : ""}`}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-2xl font-extrabold text-gold-dark">{str(row[R.ordem])}</span>
        <h3 className="text-base font-extrabold">{conta}</h3>
        <span className="tag tag-navy">{produto}</span>
        <span className="font-semibold">{usd(row[R.preco])}</span>
        <span className={`tag ${situacao === "Overdue" ? "tag-bad" : "tag-warn"}`}>{situacao === "Overdue" ? "recompra já passou" : "entrando na janela"}</span>
        {str(row[R.icp]) && <span className="tag tag-navy">{str(row[R.icp])}</span>}
        <span className="tag tag-gold">sem deal no CRM</span>
        {feito && <span className="tag tag-ok">feito hoje</span>}
      </div>
      <p className="mt-3 text-sm"><span className="font-semibold">Por quê.</span> {str(row[R.porque])}</p>
      <p className="mt-1 text-sm"><span className="font-semibold">Próxima ação.</span> {str(row[R.acao])}</p>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button className="btn-primary" disabled={pending || feito} onClick={send}>Feito: abri o deal / liguei</button>
        {msg && <span className="text-xs text-grey">{msg}</span>}
      </div>
    </article>
  );
}
