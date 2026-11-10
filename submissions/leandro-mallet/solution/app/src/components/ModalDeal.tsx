"use client";
// Modal do deal (uma tela só): linha do tempo, explicação da nota e comentários. Abre por ?deal=ID em qualquer tela.
import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { pedir } from "@/lib/cliente";
import { CONFIG } from "@/lib/config";
import { dataBR, dinheiro, rotuloSetor, ROTULO_PORTE } from "@/lib/calculos";
import type { DealDetalhe, EventoLinhaDoTempo, Tag, Usuario } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { SeloTag } from "./Dialogo";
import { Esqueleto, Estado } from "./Estado";
import { SeletorEstagio } from "./Estagio";
import { BarraNota, IconeDeal } from "./Nota";
import { NotaExplicada } from "./NotaExplicada";
import { Botao, BotaoIcone } from "./ui/Botao";
import { AreaTexto, Campo } from "./ui/Campo";
import { Seletor } from "./ui/Seletor";

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
  const [tags, setTags] = useState<Tag[]>([]);
  const [erro, setErro] = useState<{ texto: string; codigo?: string } | null>(null);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [contato, setContato] = useState<{ nome: string; cargo: string; email: string; telefone: string } | null>(null);
  const [apagando, setApagando] = useState<number | null>(null);
  const caixa = useRef<HTMLDivElement>(null);

  const fechar = useCallback(() => {
    const p = new URLSearchParams(params.toString());
    p.delete("deal");
    p.delete("secao");
    router.replace(p.size ? `${caminho}?${p}` : caminho, { scroll: false });
  }, [params, caminho, router]);

  useEffect(() => {
    let vivo = true;
    (async () => {
      const [r, t] = await Promise.all([pedir<DealDetalhe>(`/api/deals/${encodeURIComponent(id)}`), pedir<{ tags: Tag[] }>("/api/tags")]);
      if (!vivo) return;
      if (t.ok && t.dados) setTags(t.dados.tags);
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
  const secao = params.get("secao");
  useEffect(() => {
    if (d && secao === "nota") document.getElementById("t-nota")?.scrollIntoView({ block: "start" });
  }, [d, secao]);
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
    setApagando(null);
    await executar(`/api/comentarios/${comentarioId}`, "DELETE", undefined, "Comentário apagado.");
  }

  async function salvarContato() {
    if (!d || !contato?.nome.trim()) return;
    const corpo = { versao: d.atualizadoEm, nome: contato.nome, cargo: contato.cargo || null, email: contato.email || null, telefone: contato.telefone || null };
    if (await executar(`/api/deals/${d.id}/contato`, "POST", corpo, "Contato adicionado.")) setContato(null);
  }

  return (
    <div className="fixed inset-0 z-30 flex items-stretch justify-center bg-veu sm:items-center sm:p-6" role="presentation" onClick={fechar}>
      <div
        ref={caixa}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="titulo-deal"
        className="flex max-h-full w-full max-w-5xl animate-entrar flex-col overflow-hidden bg-superficie shadow-modal outline-none sm:rounded-cartao"
        onClick={(e) => e.stopPropagation()}
      >
        {erro ? (
          <div className="p-6">
            <Estado erro titulo="Não foi possível abrir este deal" texto={erro.texto}>
              <div className="flex gap-2">
                <Botao nivel="primario" onClick={() => setTentativa((t) => t + 1)}>
                  Tentar de novo
                </Botao>
                <Botao nivel="secundario" onClick={fechar}>
                  Fechar
                </Botao>
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
            <header className="border-b border-borda bg-superficie-2 px-5 py-4">
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
                <IconeDeal icone={d.icone} dias={d.diasDesdeAbertura} />
                <BotaoIcone icone="x" rotulo="Fechar" onClick={fechar} />
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
                    <Botao nivel="discreto" tamanho="compacto" icone="mais" className="px-0" onClick={() => setContato({ nome: "", cargo: "", email: "", telefone: "" })}>
                      Adicionar contato
                    </Botao>
                  )}
                </span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
                {d.tags.map((t) => (
                  <SeloTag
                    key={t.id}
                    tag={t}
                    onRemover={somenteLeitura ? undefined : () => executar(`/api/deals/${d.id}/tags?tagId=${t.id}`, "DELETE", undefined, `Tag #${t.nome} removida.`)}
                  />
                ))}
                {somenteLeitura ? null : tags.filter((t) => !d.tags.some((x) => x.id === t.id)).length ? (
                  <Seletor
                    acao
                    tamanho="compacto"
                    rotulo="Adicionar tag"
                    textoVazio="+ Tag"
                    valor=""
                    desligado={enviando}
                    onMudar={(v) => void executar(`/api/deals/${d.id}/tags`, "POST", { tagId: Number(v) }, "Tag aplicada.")}
                    opcoes={tags.filter((t) => !d.tags.some((x) => x.id === t.id)).map((t) => ({ valor: String(t.id), rotulo: `#${t.nome}` }))}
                  />
                ) : d.tags.length === 0 ? (
                  <span className="text-xs text-texto-2">Sem tags. Crie tags pela ação em lote, na tela Leads.</span>
                ) : null}
              </div>
              {contato ? (
                <div className="mt-3 flex flex-wrap items-end gap-2">
                  <label className="text-xs font-semibold">
                    Nome
                    <Campo tamanho="compacto" autoFocus value={contato.nome} maxLength={120} onChange={(e) => setContato({ ...contato, nome: e.target.value })} className="mt-1" />
                  </label>
                  <label className="text-xs font-semibold">
                    Cargo
                    <Campo tamanho="compacto" value={contato.cargo} maxLength={80} onChange={(e) => setContato({ ...contato, cargo: e.target.value })} className="mt-1" />
                  </label>
                  <label className="text-xs font-semibold">
                    E-mail (opcional)
                    <Campo tamanho="compacto" type="email" value={contato.email} maxLength={160} onChange={(e) => setContato({ ...contato, email: e.target.value })} className="mt-1" />
                  </label>
                  <label className="text-xs font-semibold">
                    Telefone (opcional)
                    <Campo tamanho="compacto" type="tel" value={contato.telefone} maxLength={25} onChange={(e) => setContato({ ...contato, telefone: e.target.value })} className="mt-1" />
                  </label>
                  <Botao nivel="secundario" tamanho="compacto" onClick={() => setContato(null)}>
                    Cancelar
                  </Botao>
                  <Botao nivel="primario" tamanho="compacto" onClick={salvarContato} disabled={enviando || !contato.nome.trim()}>
                    Salvar contato
                  </Botao>
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
                  <ol className="mt-3 border-l-2 border-borda pl-4">
                    {det.linhaDoTempo.map((e, i) => (
                      <li key={i} className="relative pb-4">
                        <span className={`absolute top-1 -left-[1.4rem] h-3 w-3 rounded-selo border-2 border-superficie ${MARCA[e.tipo]}`} aria-hidden />
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
                      <Botao key={a} nivel="secundario" tamanho="compacto" disabled={enviando} onClick={() => executar(`/api/deals/${d.id}/acoes`, "POST", { acao: a }, "Ação registrada.")}>
                        {{ liguei: "Liguei", requalifiquei: "Requalifiquei", desisti: "Desisti" }[a]}
                      </Botao>
                    ))}
                  </div>
                ) : null}
              </section>

              <div className="grid content-start gap-6">
                <section aria-labelledby="t-nota">
                  <h3 id="t-nota" className="text-base font-bold">
                    {d.score === null ? "Nota" : `Por que a nota é ${d.score}`}
                  </h3>
                  {d.score === null ? (
                    <>
                      <div className="mt-3">
                        <BarraNota score={d.score} faixa={d.faixaNota} grande />
                      </div>
                      <p className="mt-2 text-sm text-texto-2">
                        Este deal ainda não tem nota. Ela junta o encaixe do lead com o vendedor, o tempo de atendimento e o bônus da empresa, e é recalculada todo domingo.
                      </p>
                    </>
                  ) : (
                    <NotaExplicada
                      nota={d.score}
                      fit={d.fit ?? 0}
                      heat={d.heat ?? 0}
                      bonus={d.bonus ?? 0}
                      componentes={det.componentes}
                      motivos={det.motivos}
                      grupos={det.gruposDosMotivos}
                    />
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
                      <AreaTexto id="novo-comentario" value={texto} maxLength={1000} rows={2} onChange={(e) => setTexto(e.target.value)} placeholder="Escreva um comentário…" />
                      <div className="mt-2 flex justify-end">
                        <Botao nivel="primario" tamanho="compacto" onClick={postar} disabled={enviando || !texto.trim()}>
                          Postar
                        </Botao>
                      </div>
                    </div>
                  )}
                  {det.comentarios.length === 0 ? (
                    <p className="mt-2 text-sm text-texto-2">Nenhum comentário ainda.{somenteLeitura ? "" : " Escreva o primeiro."}</p>
                  ) : (
                    <ul className="mt-2 divide-y divide-divisoria">
                      {det.comentarios.map((c) => (
                        <li key={c.id} className="py-3">
                          <p className="text-sm whitespace-pre-wrap break-words">{c.texto}</p>
                          <p className="mt-1 flex items-center gap-2 text-xs text-texto-2">
                            <span>
                              {c.autor} · {dataBR(c.data)} às {hora(c.criadoEm)}
                            </span>
                            {!somenteLeitura && (c.autorId === usuario.id || usuario.papel !== "vendedor") ? (
                              apagando === c.id ? (
                                <span className="flex items-center gap-2" role="group" aria-label="Confirmar apagar">
                                  Apagar este comentário?
                                  <Botao nivel="secundario" tamanho="compacto" onClick={() => setApagando(null)}>
                                    Cancelar
                                  </Botao>
                                  <Botao nivel="primario" tamanho="compacto" onClick={() => apagar(c.id)}>
                                    Apagar
                                  </Botao>
                                </span>
                              ) : (
                                <Botao nivel="discreto" tamanho="compacto" className="h-6 px-1" onClick={() => setApagando(c.id)}>
                                  Apagar
                                </Botao>
                              )
                            ) : null}
                          </p>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </div>
            </div>

            <footer className="border-t border-borda px-5 py-3 text-xs text-texto-2">
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
