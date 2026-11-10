"use client";
// Tabela da base de leads (abertos e fechados), com seleção e ações em lote a partir do filtro.
import { useCallback, useState } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { pedir } from "@/lib/cliente";
import { CONFIG } from "@/lib/config";
import { dataBR, dinheiro, plural, ROTULO_ESTAGIO, ROTULO_MOTIVO, ROTULO_PORTE, rotuloSetor } from "@/lib/calculos";
import { HORAS_DESFAZER_LOTE, ROTULO_LOTE, type TipoLote } from "@/lib/lotes";
import type { CorTag, DealVisao, MotivoPerda, Papel, Tag } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { CORES_TAG, Dialogo, ErroFormulario, SeloTag } from "./Dialogo";
import { BarraNota, IconeDeal } from "./Nota";
import { Botao, classeBotao } from "./ui/Botao";
import { AreaTexto, Campo } from "./ui/Campo";
import { Seletor } from "./ui/Seletor";
import { classeSuperficie, Marcador } from "./ui/Superficie";

const MOTIVOS: MotivoPerda[] = ["preco", "concorrente", "sem_orcamento", "sem_resposta", "outro"];

interface Props {
  linhas: DealVisao[];
  total: number;
  papel: Papel;
  somenteLeitura: boolean;
  mostrarVendedor: boolean;
  tags: Tag[];
  filtro: { f?: string; regiao?: string; manager?: string; vendedor?: string };
}

export function TabelaLeads({ linhas, total, papel, somenteLeitura, mostrarVendedor, tags, filtro }: Props) {
  const avisos = useAvisos();
  const params = useSearchParams();
  const caminho = usePathname();
  const [marcados, setMarcados] = useState<Set<string>>(new Set());
  const [todosDoFiltro, setTodosDoFiltro] = useState(false);
  const [lote, setLote] = useState<TipoLote | null>(null);
  const [tagId, setTagId] = useState<number | "">("");
  const [novaTag, setNovaTag] = useState("");
  const [corTag, setCorTag] = useState<CorTag>("tag-1");
  const [texto, setTexto] = useState("");
  const [motivo, setMotivo] = useState<MotivoPerda | "">("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const quantidade = todosDoFiltro ? total : marcados.size;
  const podeCriarTag = (CONFIG.papeisCriarTag as readonly string[]).includes(papel);
  const link = (mud: Record<string, string>) => {
    const p = new URLSearchParams(params.toString());
    for (const [k, v] of Object.entries(mud)) p.set(k, v);
    return `${caminho}?${p}`;
  };
  const alternar = (id: string) => {
    setTodosDoFiltro(false);
    setMarcados((m) => {
      const n = new Set(m);
      if (n.has(id)) n.delete(id); else n.add(id);
      return n;
    });
  };
  const todosDaPagina = linhas.length > 0 && linhas.every((d) => marcados.has(d.id));
  const fecharLote = useCallback(() => {
    setLote(null);
    setErro(null);
  }, []);

  async function aplicar() {
    if (!lote) return;
    setErro(null);
    let idTag = tagId === "" ? undefined : tagId;
    setEnviando(true);
    if (lote === "aplicar_tag" && idTag === undefined && novaTag.trim()) {
      const r = await pedir<Tag>("/api/tags", "POST", { nome: novaTag.trim(), cor: corTag });
      if (!r.ok || !r.dados) {
        setEnviando(false);
        setErro(r.erro ?? "Não foi possível criar a tag.");
        return;
      }
      idTag = r.dados.id;
    }
    if ((lote === "aplicar_tag" || lote === "remover_tag") && idTag === undefined) {
      setEnviando(false);
      setErro("Escolha a tag.");
      return;
    }
    if (lote === "comentar" && !texto.trim()) {
      setEnviando(false);
      setErro("Escreva o comentário.");
      return;
    }
    const r = await pedir<{ loteId: number; aplicados: number; pulados: number }>("/api/lotes", "POST", {
      tipo: lote,
      ...(todosDoFiltro ? { filtro } : { ids: [...marcados] }),
      tagId: idTag,
      texto: lote === "comentar" ? texto : undefined,
      motivo: lote === "encerrar_perdido" ? motivo || null : undefined,
    });
    setEnviando(false);
    if (!r.ok || !r.dados) {
      setErro(r.erro ?? "Não foi possível aplicar o lote.");
      return;
    }
    const { aplicados, pulados, loteId } = r.dados;
    avisos.ok(`${ROTULO_LOTE[lote]}: ${plural(aplicados, "lead", "leads")}${pulados ? `; ${pulados} não se aplicavam` : ""}.`, `lote:${loteId}`);
    setMarcados(new Set());
    setTodosDoFiltro(false);
    setTexto("");
    setNovaTag("");
    setTagId("");
    fecharLote();
    avisos.atualizar();
  }

  const exemplos = (todosDoFiltro ? linhas : linhas.filter((d) => marcados.has(d.id))).slice(0, 5);

  return (
    <div className="grid gap-3">
      {quantidade > 0 && !somenteLeitura ? (
        <div className={`${classeSuperficie} sticky top-2 z-10 flex flex-wrap items-center gap-2 border-marinho px-3 py-2 shadow-menu`} role="region" aria-label="Ações em lote">
          <span className="text-sm font-semibold">{plural(quantidade, "selecionado", "selecionados")}</span>
          {!todosDoFiltro && total > marcados.size ? (
            <Botao nivel="discreto" tamanho="compacto" onClick={() => setTodosDoFiltro(true)}>
              Selecionar os {total.toLocaleString("pt-BR")} do filtro
            </Botao>
          ) : null}
          <span className="flex-1" />
          {(Object.keys(ROTULO_LOTE) as TipoLote[]).map((t) => (
            <Botao key={t} nivel="secundario" tamanho="compacto" onClick={() => setLote(t)}>
              {ROTULO_LOTE[t]}
            </Botao>
          ))}
          <Botao
            nivel="discreto"
            tamanho="compacto"
            onClick={() => {
              setMarcados(new Set());
              setTodosDoFiltro(false);
            }}
          >
            Limpar seleção
          </Botao>
        </div>
      ) : null}

      <div className={`${classeSuperficie} relative overflow-x-auto`}>
        <table className="w-full table-fixed text-sm">
          <colgroup>
            {somenteLeitura ? null : <col className="w-11" />}
            <col className="w-60" />
            {mostrarVendedor ? <col className="w-40" /> : null}
            <col className="w-40" />
            <col className="w-34" />
            <col className="w-38" />
            <col className="w-26" />
            <col className="w-28" />
            <col className="min-w-24" />
          </colgroup>
          <thead>
            <tr className="h-10 border-b border-borda bg-superficie-2 text-left text-xs text-texto-2">
              {somenteLeitura ? null : (
                <th className="px-3">
                  <Marcador
                    rotulo="Selecionar todos desta página"
                    checked={todosDaPagina}
                    onChange={() => {
                      setTodosDoFiltro(false);
                      setMarcados(todosDaPagina ? new Set() : new Set(linhas.map((d) => d.id)));
                    }}
                  />
                </th>
              )}
              <th className="px-3 py-2 font-semibold">Lead</th>
              {mostrarVendedor ? <th className="px-3 py-2 font-semibold">Vendedor</th> : null}
              <th className="px-3 py-2 font-semibold">Estágio</th>
              <th className="px-3 py-2 font-semibold">Nota</th>
              <th className="px-3 py-2 text-right font-semibold">Valor</th>
              <th className="px-3 py-2 font-semibold">Abertura</th>
              <th className="px-3 py-2 font-semibold">Último contato</th>
              <th className="px-3 py-2 font-semibold">Tags</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map((d) => {
              const aberto = d.estagio === "Prospecting" || d.estagio === "Engaging";
              return (
                <tr key={d.id} className={`h-14 border-b border-divisoria last:border-0 ${todosDoFiltro || marcados.has(d.id) ? "bg-tom-destaque/40" : "hover:bg-superficie-2"}`}>
                  {somenteLeitura ? null : (
                    <td className="px-3">
                      <Marcador rotulo={`Selecionar ${d.nome}`} checked={todosDoFiltro || marcados.has(d.id)} onChange={() => alternar(d.id)} />
                    </td>
                  )}
                  <td className="px-3">
                    <span className="flex items-center gap-2">
                      <span className="min-w-0 flex-1">
                        <Link href={link({ deal: d.id })} scroll={false} title={d.nome} className="block truncate font-semibold hover:underline">
                          {d.nome}
                        </Link>
                        <span className="block truncate text-xs text-texto-2">
                          {d.contato ? d.contato.nome : "Sem contato"}
                          {d.setor ? ` · ${rotuloSetor(d.setor)}${d.porte ? `, ${ROTULO_PORTE[d.porte]}` : ""}` : ""}
                        </span>
                      </span>
                    </span>
                  </td>
                  {mostrarVendedor ? <td className="truncate px-3" title={d.vendedor}>{d.vendedor}</td> : null}
                  <td className="px-3 whitespace-nowrap">
                    {ROTULO_ESTAGIO[d.estagio]}
                    {d.motivoPerda ? <span className="block truncate text-xs text-texto-2">{ROTULO_MOTIVO[d.motivoPerda]}</span> : null}
                    {d.icone ? (
                      <span className="mt-0.5 block">
                        <IconeDeal icone={d.icone} dias={d.diasDesdeAbertura} />
                      </span>
                    ) : null}
                  </td>
                  <td className="px-3">{aberto ? <BarraNota score={d.score} faixa={d.faixaNota} /> : <span className="text-texto-2">—</span>}</td>
                  <td className="px-3 text-right whitespace-nowrap tabular-nums">
                    {dinheiro(aberto ? d.valorEsperado : d.closeValue)}{" "}
                    <span className="text-xs text-texto-2">{aberto ? (d.valorPeloPrecoDeTabela ? "preço de tabela" : "esperado") : d.estagio === "Won" ? "fechamento" : ""}</span>
                  </td>
                  <td className="px-3 whitespace-nowrap tabular-nums">{d.dataAbertura ? dataBR(d.dataAbertura) : "Não iniciado"}</td>
                  <td className="px-3 whitespace-nowrap tabular-nums">{d.ultimoContato ? dataBR(d.ultimoContato) : "Sem contato"}</td>
                  <td className="px-3">
                    <span className="flex max-h-12 flex-wrap items-center gap-1 overflow-hidden">
                      {d.tags.map((t) => (
                        <SeloTag key={t.id} tag={t} />
                      ))}
                      {d.qtdComentarios ? <span className="text-xs text-texto-2">{plural(d.qtdComentarios, "comentário", "comentários")}</span> : null}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {total > linhas.length ? (
        <Link href={link({ n: String(linhas.length + CONFIG.porPagina) })} scroll={false} className={classeBotao("secundario", "normal", "w-full")}>
          Mostrar mais ({(total - linhas.length).toLocaleString("pt-BR")} restantes)
        </Link>
      ) : null}

      {lote ? (
        <Dialogo titulo={`${ROTULO_LOTE[lote]} em ${plural(quantidade, "lead", "leads")}`} onFechar={fecharLote}>
          <div className="grid gap-3">
            {lote === "aplicar_tag" || lote === "remover_tag" ? (
              <div className="grid gap-1 text-sm font-semibold">
                <span aria-hidden>Tag</span>
                <Seletor
                  rotulo="Tag"
                  valor={tagId === "" ? "" : String(tagId)}
                  onMudar={(v) => setTagId(v ? Number(v) : "")}
                  textoVazio={tags.length ? "Escolha a tag" : "Nenhuma tag criada ainda"}
                  className="w-full font-normal"
                  opcoes={[{ valor: "", rotulo: tags.length ? "Escolha a tag" : "Nenhuma tag criada ainda" }, ...tags.map((t) => ({ valor: String(t.id), rotulo: `#${t.nome}` }))]}
                />
              </div>
            ) : null}
            {lote === "aplicar_tag" && podeCriarTag && tagId === "" ? (
              <div className="rounded-controle bg-superficie-2 p-3">
                <label className="grid gap-1 text-sm font-semibold">
                  Ou crie uma tag nova
                  <Campo value={novaTag} maxLength={30} onChange={(e) => setNovaTag(e.target.value)} placeholder="ex.: urgente" />
                </label>
                <div className="mt-2 flex items-center gap-2" role="radiogroup" aria-label="Cor da tag">
                  {CORES_TAG.map((c) => (
                    <button key={c} role="radio" aria-checked={corTag === c} aria-label={`Cor ${c.slice(4)}`} onClick={() => setCorTag(c)} className={`rounded-selo p-1 ${corTag === c ? "ring-2 ring-marinho" : "ring-1 ring-transparent hover:ring-borda"}`}>
                      <SeloTag tag={{ nome: novaTag.trim() || "tag", cor: c }} />
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
            {lote === "aplicar_tag" && !podeCriarTag && tags.length === 0 ? <p className="text-sm text-texto-2">Tags novas são criadas pelo manager ou pelo admin.</p> : null}
            {lote === "comentar" ? (
              <label className="grid gap-1 text-sm font-semibold">
                Comentário (o mesmo em todos)
                <AreaTexto value={texto} maxLength={1000} rows={3} onChange={(e) => setTexto(e.target.value)} />
              </label>
            ) : null}
            {lote === "encerrar_perdido" ? (
              <div className="grid gap-1 text-sm font-semibold">
                <span aria-hidden>Motivo da perda (opcional)</span>
                <Seletor
                  rotulo="Motivo da perda (opcional)"
                  valor={motivo}
                  onMudar={(v) => setMotivo(v as MotivoPerda | "")}
                  className="w-full font-normal"
                  opcoes={[{ valor: "", rotulo: "Não informar" }, ...MOTIVOS.map((m) => ({ valor: m, rotulo: ROTULO_MOTIVO[m] }))]}
                />
              </div>
            ) : null}
            <div className="text-sm">
              <p className="font-semibold">Vai valer para {plural(quantidade, "lead", "leads")}. Exemplos:</p>
              <ul className="mt-1 list-disc pl-5 text-texto-2">
                {exemplos.map((d) => (
                  <li key={d.id}>{d.nome}</li>
                ))}
              </ul>
              <p className="mt-2 text-xs text-texto-2">
                Os leads em que a ação não se aplica são pulados e contados. Dá para desfazer pelo aviso que aparece em seguida ou, por {HORAS_DESFAZER_LOTE} horas, em Lotes recentes.
              </p>
            </div>
            <ErroFormulario texto={erro} />
            <div className="flex justify-end gap-2">
              <Botao nivel="secundario" onClick={fecharLote}>
                Cancelar
              </Botao>
              <Botao nivel="primario" onClick={aplicar} disabled={enviando}>
                {enviando ? "Aplicando…" : `${ROTULO_LOTE[lote]} em ${quantidade.toLocaleString("pt-BR")}`}
              </Botao>
            </div>
          </div>
        </Dialogo>
      ) : null}
    </div>
  );
}
