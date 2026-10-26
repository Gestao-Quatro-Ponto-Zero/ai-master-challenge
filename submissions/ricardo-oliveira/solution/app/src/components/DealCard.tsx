"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { registrar, type Acao } from "@/lib/actions";
import type { Row } from "@/lib/types";
import { L } from "@/lib/types";
import { num, str, bool, usd } from "@/lib/parse";

export function DealCard({ row, readOnly }: { row: Row; readOnly?: boolean }) {
  const router = useRouter();
  const [pending, start] = useTransition();
  const [msg, setMsg] = useState<string | null>(null);
  const [askValue, setAskValue] = useState(false);
  const [valor, setValor] = useState<string>(String(Math.round(num(row[L.preco]))));

  const id = str(row[L.id]);
  const passo = num(row[L.passo]);
  const vivo = str(row[L.vivo]);
  const feito = bool(row[L.feitoHoje]);
  const recompra = str(row[L.recompra]);
  const comprasDepois = num(row[L.comprasDepois]);
  const intervalo = str(row[L.intervalo]);
  const ultimaCompra = str(row[L.ultimaCompra]);
  const separado = bool(row[L.separado]);

  const send = (acao: Acao, v?: number) =>
    start(async () => {
      const r = await registrar(id, acao, v);
      setMsg(r?.error ? `Erro: ${r.error}` : acao === "feito" ? "Marcado como feito. Vai pro fim da lista de hoje." : acao === "separado" ? "Demanda separada confirmada. O deal volta pros passos." : `Registrado como ${acao}. Sai da lista.`);
      setAskValue(false);
      // A planilha recalcula em um ou dois segundos; recarrega a lista depois disso.
      if (!r?.error) setTimeout(() => router.refresh(), 2500);
    });

  const recompraTag = recompra === "Fora da janela" ? "tag-bad" : recompra === "Entrando na janela" ? "tag-warn" : "tag-navy";

  return (
    <article className={`card p-4 ${feito ? "opacity-60" : ""}`}>
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-2xl font-extrabold text-gold-dark">{str(row[L.ordem])}</span>
            <h3 className="text-base font-extrabold">{str(row[L.conta])}</h3>
            <span className="tag tag-navy">{str(row[L.produto])}</span>
            <span className="font-semibold">{usd(row[L.preco])}</span>
          </div>
          <div className="mt-1 flex gap-2 flex-wrap text-xs">
            <span className="tag tag-gold">Passo {passo}</span>
            <span className={`tag ${vivo === "Vivo" ? "tag-ok" : vivo === "Sem data" ? "tag-navy" : "tag-bad"}`}>{vivo}</span>
            <span className={`tag ${recompraTag}`}>{recompra}</span>
            {str(row[L.icp]) && <span className="tag tag-navy">{str(row[L.icp])}</span>}
            {comprasDepois > 0 && !separado && <span className="tag tag-bad">outro vendedor fechou depois de abrir</span>}
            {separado && <span className="tag tag-ok">demanda separada confirmada</span>}
            {feito && <span className="tag tag-ok">feito hoje</span>}
          </div>
        </div>
        <div className="text-xs text-grey text-right">
          <div>{id}</div>
          {intervalo && <div>recompra a cada {intervalo} dias · última há {ultimaCompra}</div>}
          {str(row[L.vendedorAtual]) !== str(row[L.trabalha]) && <div>veio de {str(row[L.vendedorAtual])}</div>}
        </div>
      </div>
      <p className="mt-3 text-sm"><span className="font-semibold">Por quê.</span> {str(row[L.porque])}</p>
      <p className="mt-1 text-sm"><span className="font-semibold">Próxima ação.</span> {str(row[L.acao])}</p>
      {!readOnly && passo === 5 && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button className="btn-primary" disabled={pending} onClick={() => send("separado")}>Demanda separada: volta pros passos</button>
          <button className="btn-secondary" disabled={pending} onClick={() => send("perdido")}>Mesmo pedido: fechar como perdido</button>
          <button className="btn-ghost" disabled={pending || feito} onClick={() => send("feito")}>Feito (confirmação pedida)</button>
          {msg && <span className="text-xs text-grey">{msg}</span>}
        </div>
      )}
      {!readOnly && passo !== 5 && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button className="btn-primary" disabled={pending || feito} onClick={() => send("feito")}>Feito</button>
          {!askValue ? (
            <button className="btn-secondary" disabled={pending} onClick={() => setAskValue(true)}>Ganho</button>
          ) : (
            <span className="flex items-center gap-2">
              <input className="border border-line rounded-lg px-2 py-1 w-28" value={valor} onChange={(e) => setValor(e.target.value)} />
              <button className="btn-primary" disabled={pending} onClick={() => send("ganho", num(valor))}>Confirmar ganho</button>
              <button className="btn-ghost" onClick={() => setAskValue(false)}>Cancelar</button>
            </span>
          )}
          <button className="btn-ghost" disabled={pending} onClick={() => send("perdido")}>Perdido</button>
          {msg && <span className="text-xs text-grey">{msg}</span>}
        </div>
      )}
    </article>
  );
}
