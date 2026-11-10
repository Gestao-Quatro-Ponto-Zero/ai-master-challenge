"use client";
// Modal do deal (uma tela só): linha do tempo, explicação da nota e comentários. Abre por ?deal=ID em qualquer tela.
import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { pedir } from "@/lib/cliente";
import { CONFIG } from "@/lib/config";
import { dataBR, dinheiro, rotuloSetor, ROTULO_PORTE } from "@/lib/calculos";
import type { DealDetalhe, EventoLinhaDoTempo, Usuario } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { Esqueleto, Estado } from "./Estado";
import { SeletorEstagio } from "./Estagio";
import { BarraNota, IconeDeal } from "./Nota";

const MARCA: Record<EventoLinhaDoTempo["tipo"], string> = {
  aberto: "bg-marinho",
  fechado: "bg-marinho",
  estagio: "bg-marinho",
  criado: "bg-dourado",
  dados: "bg-dourado-medio",
  acao: "bg-bronze",
  comentario: "bg-dourado-claro",
  tag: "bg-cinza",
  repasse: "bg-bronze-escuro",
};

const hora = (iso: string | null) => (iso ? new Date(iso).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }) : null);

export function ModalDeal({ usuario, somenteLeitura }: { usuario: Usuario; somenteLeitura: boolean }) {
  const id = useSearchParams().get("deal");
  // A chave remonta o conteúdo a cada deal: o estado do modal anterior não vaza para o próximo.
  return id ? <Conteudo key={id} id={id} usuario={usuario} somenteLeitura={somenteLeitura} /> : null;
}

function Conteudo({ id, usuario, somenteLeitura }: { id: string; usuario: Usuario; somenteLeitura: boolean }) {
  const params = useSearchParams();
  const caminho = usePathname();
  const router = useRouter();
  const avisos = useAvisos();
  const [tentativa, setTentativa] = useState(0);
  const [det, setDet] = useState<DealDetalhe | null>(null);
  const [erro, setErro] = useState<{ texto: string; codigo?: string } | null>(null);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [contato, setContato] = useState<{ nome: string; cargo: string } | null>(null);
  const caixa = useRef<HTMLDivElement>(null);

  const fechar = useCallback(() => {
    const p = new URLSearchParams(params.toString());
    p.delete("deal");
    router.replace(p.size ? `${caminho}?${p}` : caminho, { scroll: false });
  }, [params, caminho, router]);

  useEffect(() => {
    let vivo = true;
    (async () => {
      const r = await pedir<DealDetalhe>(`/api/deals/${encodeURIComponent(id)}`);
      if (!vivo) return;
      if (r.ok && r.dados) {
        setDet(r.dados);
        setErro(null);
      } else setErro({ texto: r.erro ?? "Não foi possível abrir este deal.", codigo: r.codigo });
    })();
    return () => {
      vivo = false;
    };
  }, [id, tentativa, avisos.revisao]);

  useEffect(() => {
    caixa.current?.focus();
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && fechar();
    document.addEventListener("keydown", tecla);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", tecla);
      document.body.style.overflow = "";
    };
  }, [fechar]);

  const d = det?.deal.id === id ? det.deal : null;
  const aberto = d ? d.estagio === "Prospecting" || d.estagio === "Engaging" : false;

  async function executar(url: string, metodo: "POST" | "DELETE", corpo: unknown, feito: string) {
    setEnviando(true);
    const r = await pedir<{ desfazer?: string | null }>(url, metodo, corpo);
    setEnviando(false);
    if (r.ok) {
      avisos.ok(feito, r.dados?.desfazer);
      avisos.atualizar();
    } else avisos.erro(r.erro ?? "Não foi possível salvar. Tente de novo.", r.codigo);
    return r.ok;
  }

  async function postar() {
    if (!d || !texto.trim()) return;
    if (await executar(`/api/deals/${d.id}/comentarios`, "POST", { texto }, "Comentário publicado.")) setTexto("");
  }

  async function apagar(comentarioId: number) {
    if (!window.confirm("Apagar este comentário? Ele some da tela e da linha do tempo.")) return;
    await executar(`/api/comentarios/${comentarioId}`, "DELETE", undefined, "Comentário apagado.");
  }

  async function salvarContato() {
    if (!d || !contato?.nome.trim()) return;
    if (await executar(`/api/deals/${d.id}/contato`, "POST", { versao: d.atualizadoEm, nome: contato.nome, cargo: contato.cargo || null }, "Contato adicionado.")) setContato(null);
  }

  return (
    <div className="fixed inset-0 z-30 flex items-stretch justify-center bg-veu sm:items-center sm:p-6" role="presentation" onClick={fechar}>
      <div
        ref={caixa}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-deal"
        className="flex max-h-full w-full max-w-5xl animate-entrar flex-col overflow-hidden bg-fundo shadow-modal outline-none sm:rounded-cartao"
        onClick={(e) => e.stopPropagation()}
      >
        {erro ? (
          <div className="p-6">
            <Estado erro titulo="Não foi possível abrir este deal" texto={erro.texto}>
              <div className="flex gap-2">
                <button onClick={() => setTentativa((t) => t + 1)} className="rounded-controle bg-marinho px-4 py-2 text-sm font-semibold text-branco">
                  Tentar de novo
                </button>
                <button onClick={fechar} className="rounded-controle border border-linha-forte px-4 py-2 text-sm font-semibold">
                  Fechar
                </button>
              </div>
              {erro.codigo ? <p className="text-xs text-texto-2">Código para suporte: {erro.codigo}</p> : null}
            </Estado>
          </div>
        ) : !d || !det ? (
          <div className="grid gap-4 p-6" aria-busy="true" aria-label="Carregando o deal">
            <Esqueleto className="h-8 w-2/3" />
            <Esqueleto className="h-4 w-1/2" />
            <div className="grid gap-6 md:grid-cols-2">
              <Esqueleto className="h-64" />
              <Esqueleto className="h-64" />
            </div>
          </div>
        ) : (
          <>
            <header className="border-b border-linha bg-marfim px-5 py-4">
              <div className="flex items-start gap-3">
                <div className="min-w-0 flex-1">
                  <h2 id="titulo-deal" className="text-xl font-bold break-words">
                    {d.nome}
                  </h2>
                  <p className="mt-1 text-sm text-texto-2">
                    {d.vendedor} · time de {d.manager} · {d.regiao}
                    {d.setor ? ` · ${rotuloSetor(d.setor)}${d.porte ? `, ${ROTULO_PORTE[d.porte]}` : ""}` : ""}
                  </p>
                </div>
                <IconeDeal icone={d.icone} dias={d.diasDesdeAbertura} comRotulo />
                <button onClick={fechar} aria-label="Fechar" className="rounded-controle border border-linha-forte px-3 py-1 text-lg leading-none">
                  ×
                </button>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm">
                <SeletorEstagio deal={d} papel={usuario.papel} desligado={somenteLeitura} />
                <span>
                  <strong>{dinheiro(d.valorEsperado ?? d.closeValue)}</strong>{" "}
                  <span className="text-texto-2">{aberto ? (d.valorPeloPrecoDeTabela ? "pelo preço de tabela" : "esperado") : "fechamento"}</span>
                </span>
                <span className="text-texto-2">
                  {d.dataAbertura ? `Aberto em ${dataBR(d.dataAbertura)}${d.diasDesdeAbertura !== null ? ` · ${d.diasDesdeAbertura} dias` : ""}` : "Não iniciado"}
                </span>
                <span>
                  {det.contatoCompleto ? (
                    <>
                      <strong>{det.contatoCompleto.nome}</strong>
                      {det.contatoCompleto.cargo ? <span className="text-texto-2">, {det.contatoCompleto.cargo}</span> : null}
                    </>
                  ) : somenteLeitura ? (
                    <span className="text-texto-2">Sem contato</span>
                  ) : (
                    <button onClick={() => setContato({ nome: "", cargo: "" })} className="font-semibold text-bronze-escuro underline">
                      + Adicionar contato
                    </button>
                  )}
                </span>
              </div>
              {contato ? (
                <div className="mt-3 flex flex-wrap items-end gap-2">
                  <label className="text-xs font-semibold">
                    Nome
                    <input autoFocus value={contato.nome} maxLength={120} onChange={(e) => setContato({ ...contato, nome: e.target.value })} className="mt-1 block rounded-controle border border-linha-forte px-2 py-1 text-sm font-normal" />
                  </label>
                  <label className="text-xs font-semibold">
                    Cargo
                    <input value={contato.cargo} maxLength={80} onChange={(e) => setContato({ ...contato, cargo: e.target.value })} className="mt-1 block rounded-controle border border-linha-forte px-2 py-1 text-sm font-normal" />
                  </label>
                  <button onClick={salvarContato} disabled={enviando || !contato.nome.trim()} className="rounded-controle bg-marinho px-3 py-1 text-sm font-semibold text-branco disabled:opacity-50">
                    Salvar contato
                  </button>
                  <button onClick={() => setContato(null)} className="rounded-controle border border-linha-forte px-3 py-1 text-sm">
                    Cancelar
                  </button>
                </div>
              ) : null}
            </header>

            <div className="grid flex-1 gap-6 overflow-y-auto px-5 py-5 md:grid-cols-2">
              <section aria-labelledby="t-linha">
                <h3 id="t-linha" className="text-base font-bold">
                  Linha do tempo
                </h3>
                {det.linhaDoTempo.length === 0 ? (
                  <p className="mt-3 text-sm text-texto-2">Sem registros ainda. O primeiro contato aparece aqui.</p>
                ) : (
                  <ol className="mt-3 border-l-2 border-linha-forte pl-4">
                    {det.linhaDoTempo.map((e, i) => (
                      <li key={i} className="relative pb-4">
                        <span className={`absolute top-1 -left-6 h-3 w-3 rounded-selo border-2 border-fundo ${MARCA[e.tipo]}`} aria-hidden />
                        <p className={`text-sm ${e.desfeito ? "text-texto-2 line-through" : ""}`}>{e.descricao}</p>
                        <p className="text-xs text-texto-2">
                          {dataBR(e.data)}
                          {e.momento ? ` às ${hora(e.momento)}` : ""}
                          {e.autor ? ` · ${e.autor}` : ""}
                          {e.desfeito ? " · desfeito" : ""}
                        </p>
                      </li>
                    ))}
                    {aberto && d.dataAbertura && det.linhaDoTempo.length === 1 ? (
                      <li className="pb-2 text-xs text-texto-2">Sem registros entre {dataBR(d.dataAbertura)} e hoje.</li>
                    ) : null}
                  </ol>
                )}
                {aberto && !somenteLeitura ? (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {(["liguei", "requalifiquei", "desisti"] as const).map((a) => (
                      <button
                        key={a}
                        disabled={enviando}
                        onClick={() => executar(`/api/deals/${d.id}/acoes`, "POST", { acao: a }, "Ação registrada.")}
                        className="rounded-controle border border-marinho px-3 py-1 text-sm font-semibold disabled:opacity-50"
                      >
                        {{ liguei: "Liguei", requalifiquei: "Requalifiquei", desisti: "Desisti" }[a]}
                      </button>
                    ))}
                  </div>
                ) : null}
              </section>

              <div className="grid content-start gap-6">
                <section aria-labelledby="t-nota">
                  <h3 id="t-nota" className="text-base font-bold">
                    {d.score === null ? "Nota" : `Por que a nota é ${d.score}`}
                  </h3>
                  <div className="mt-3">
                    <BarraNota score={d.score} faixa={d.faixaNota} grande />
                  </div>
                  {d.score === null ? (
                    <p className="mt-2 text-sm text-texto-2">
                      Este deal ainda não tem nota. Ela junta o encaixe com o vendedor (FIT), o tempo de atendimento (HEAT) e o bônus da empresa, e é recalculada todo domingo.
                    </p>
                  ) : (
                    <>
                      <dl className="mt-3 grid grid-cols-3 gap-2 text-center text-sm">
                        {(
                          [
                            ["FIT", d.fit],
                            ["HEAT", d.heat],
                            ["Bônus", d.bonus],
                          ] as const
                        ).map(([rot, v]) => (
                          <div key={rot} className="rounded-controle border border-linha px-2 py-2">
                            <dt className="text-xs text-texto-2">{rot}</dt>
                            <dd className="font-titulo text-lg font-bold">{v ?? "—"}</dd>
                          </div>
                        ))}
                      </dl>
                      <ul className="mt-3 list-disc pl-5 text-sm">
                        {det.motivos.map((m, i) => (
                          <li key={i}>{m}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </section>

                <section aria-labelledby="t-coment">
                  <h3 id="t-coment" className="text-base font-bold">
                    Comentários
                  </h3>
                  {somenteLeitura ? null : (
                    <div className="mt-3">
                      <label className="sr-only" htmlFor="novo-comentario">
                        Novo comentário
                      </label>
                      <textarea
                        id="novo-comentario"
                        value={texto}
                        maxLength={1000}
                        rows={2}
                        onChange={(e) => setTexto(e.target.value)}
                        placeholder="Escreva um comentário…"
                        className="w-full rounded-controle border border-linha-forte px-3 py-2 text-sm"
                      />
                      <div className="mt-1 flex justify-end">
                        <button onClick={postar} disabled={enviando || !texto.trim()} className="rounded-controle border border-marinho px-3 py-1 text-sm font-semibold disabled:opacity-50">
                          Postar
                        </button>
                      </div>
                    </div>
                  )}
                  {det.comentarios.length === 0 ? (
                    <p className="mt-2 text-sm text-texto-2">Nenhum comentário ainda.{somenteLeitura ? "" : " Escreva o primeiro."}</p>
                  ) : (
                    <ul className="mt-2 grid gap-2">
                      {det.comentarios.map((c) => (
                        <li key={c.id} className="rounded-controle border border-linha bg-marfim px-3 py-2">
                          <p className="text-sm whitespace-pre-wrap break-words">{c.texto}</p>
                          <p className="mt-1 flex items-center gap-2 text-xs text-texto-2">
                            <span>
                              {c.autor} · {dataBR(c.data)} às {hora(c.criadoEm)}
                            </span>
                            {!somenteLeitura && (c.autorId === usuario.id || usuario.papel !== "vendedor") ? (
                              <button onClick={() => apagar(c.id)} className="font-semibold text-bronze-escuro underline">
                                Apagar
                              </button>
                            ) : null}
                          </p>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </div>
            </div>

            <footer className="border-t border-linha px-5 py-3 text-xs text-texto-2">
              <details>
                <summary className="cursor-pointer">Ver detalhes</summary>
                <p className="mt-1">
                  Código do deal: {d.id} · produto {d.produto} (série {d.serie}), preço de tabela {dinheiro(d.preco)} · dados até {dataBR(CONFIG.dataReferencia)}
                </p>
              </details>
            </footer>
          </>
        )}
      </div>
    </div>
  );
}
