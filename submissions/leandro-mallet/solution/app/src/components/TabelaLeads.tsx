"use client";
// Tabela da base de leads (abertos e fechados), com seleção e ações em lote a partir do filtro.
import { useCallback, useState } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { pedir } from "@/lib/cliente";
import { CONFIG } from "@/lib/config";
import { dataBR, dinheiro, plural, ROTULO_ESTAGIO, ROTULO_MOTIVO, ROTULO_PORTE, rotuloSetor } from "@/lib/calculos";
import type { CorTag, DealVisao, MotivoPerda, Papel, Tag } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { botaoNeutro, botaoPrincipal, botaoSecundario, campo, CORES_TAG, Dialogo, ErroFormulario, SeloTag } from "./Dialogo";
import { BarraNota, IconeDeal } from "./Nota";

type TipoLote = "aplicar_tag" | "remover_tag" | "comentar" | "avancar_estagio" | "encerrar_perdido";
const ROTULO_LOTE: Record<TipoLote, string> = {
  aplicar_tag: "Aplicar tag",
  remover_tag: "Remover tag",
  comentar: "Comentar",
  avancar_estagio: "Mover para Em negociação",
  encerrar_perdido: "Encerrar como perdido",
};
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
        <div className="sticky top-2 z-10 flex flex-wrap items-center gap-2 rounded-cartao border border-marinho bg-marfim px-3 py-2 shadow-cartao" role="region" aria-label="Ações em lote">
          <span className="text-sm font-semibold">{plural(quantidade, "selecionado", "selecionados")}</span>
          {!todosDoFiltro && total > marcados.size ? (
            <button onClick={() => setTodosDoFiltro(true)} className="text-sm text-bronze-escuro underline">
              Selecionar os {total.toLocaleString("pt-BR")} do filtro
            </button>
          ) : null}
          <span className="flex-1" />
          {(Object.keys(ROTULO_LOTE) as TipoLote[]).map((t) => (
            <button key={t} onClick={() => setLote(t)} className={botaoSecundario}>
              {ROTULO_LOTE[t]}
            </button>
          ))}
          <button
            onClick={() => {
              setMarcados(new Set());
              setTodosDoFiltro(false);
            }}
            className={botaoNeutro}
          >
            Limpar seleção
          </button>
        </div>
      ) : null}

      <div className="overflow-x-auto rounded-cartao border border-linha bg-fundo shadow-cartao">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b-2 border-marinho bg-marfim text-left text-xs text-texto-2">
              {somenteLeitura ? null : (
                <th className="px-3 py-2">
                  <input
                    type="checkbox"
                    aria-label="Selecionar todos desta página"
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
                <tr key={d.id} className={`border-b border-linha align-top ${todosDoFiltro || marcados.has(d.id) ? "bg-marfim" : ""}`}>
                  {somenteLeitura ? null : (
                    <td className="px-3 py-2">
                      <input type="checkbox" aria-label={`Selecionar ${d.nome}`} checked={todosDoFiltro || marcados.has(d.id)} onChange={() => alternar(d.id)} />
                    </td>
                  )}
                  <td className="max-w-72 min-w-52 px-3 py-2">
                    <span className="flex items-start gap-2">
                      <span className="min-w-0">
                        <Link href={link({ deal: d.id })} scroll={false} className="font-semibold break-words hover:underline">
                          {d.nome}
                        </Link>
                        <span className="block text-xs text-texto-2">
                          {d.contato ? d.contato.nome : "Sem contato"}
                          {d.setor ? ` · ${rotuloSetor(d.setor)}${d.porte ? `, ${ROTULO_PORTE[d.porte]}` : ""}` : ""}
                        </span>
                      </span>
                      <IconeDeal icone={d.icone} dias={d.diasDesdeAbertura} />
                    </span>
                  </td>
                  {mostrarVendedor ? <td className="px-3 py-2 whitespace-nowrap">{d.vendedor}</td> : null}
                  <td className="px-3 py-2 whitespace-nowrap">
                    {ROTULO_ESTAGIO[d.estagio]}
                    {d.motivoPerda ? <span className="block text-xs text-texto-2">{ROTULO_MOTIVO[d.motivoPerda]}</span> : null}
                  </td>
                  <td className="min-w-32 px-3 py-2">{aberto ? <BarraNota score={d.score} faixa={d.faixaNota} /> : <span className="text-texto-2">—</span>}</td>
                  <td className="px-3 py-2 text-right whitespace-nowrap">
                    {dinheiro(aberto ? d.valorEsperado : d.closeValue)}
                    <span className="block text-xs text-texto-2">{aberto ? (d.valorPeloPrecoDeTabela ? "preço de tabela" : "esperado") : d.estagio === "Won" ? "fechamento" : ""}</span>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">{d.dataAbertura ? dataBR(d.dataAbertura) : "Não iniciado"}</td>
                  <td className="px-3 py-2 whitespace-nowrap">{d.ultimoContato ? dataBR(d.ultimoContato) : "Sem contato"}</td>
                  <td className="px-3 py-2">
                    <span className="flex flex-wrap items-center gap-1">
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
        <Link href={link({ n: String(linhas.length + CONFIG.porPagina) })} scroll={false} className={`${botaoNeutro} text-center font-semibold`}>
          Mostrar mais ({(total - linhas.length).toLocaleString("pt-BR")} restantes)
        </Link>
      ) : null}

      {lote ? (
        <Dialogo titulo={`${ROTULO_LOTE[lote]} em ${plural(quantidade, "lead", "leads")}`} onFechar={fecharLote}>
          <div className="grid gap-3">
            {lote === "aplicar_tag" || lote === "remover_tag" ? (
              <label className="text-sm font-semibold">
                Tag
                <select value={tagId} onChange={(e) => setTagId(e.target.value ? Number(e.target.value) : "")} className={campo}>
                  <option value="">{tags.length ? "Escolha a tag" : "Nenhuma tag criada ainda"}</option>
                  {tags.map((t) => (
                    <option key={t.id} value={t.id}>
                      #{t.nome}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            {lote === "aplicar_tag" && podeCriarTag && tagId === "" ? (
              <div className="rounded-controle border border-linha bg-marfim p-3">
                <label className="text-sm font-semibold">
                  Ou crie uma tag nova
                  <input value={novaTag} maxLength={30} onChange={(e) => setNovaTag(e.target.value)} placeholder="ex.: urgente" className={campo} />
                </label>
                <div className="mt-2 flex items-center gap-2" role="radiogroup" aria-label="Cor da tag">
                  {CORES_TAG.map((c) => (
                    <button key={c} role="radio" aria-checked={corTag === c} aria-label={`Cor ${c.slice(4)}`} onClick={() => setCorTag(c)} className={`rounded-selo p-1 ${corTag === c ? "ring-2 ring-marinho" : ""}`}>
                      <SeloTag tag={{ nome: novaTag.trim() || "tag", cor: c }} />
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
            {lote === "aplicar_tag" && !podeCriarTag && tags.length === 0 ? <p className="text-sm text-texto-2">Tags novas são criadas pelo manager ou pelo admin.</p> : null}
            {lote === "comentar" ? (
              <label className="text-sm font-semibold">
                Comentário (o mesmo em todos)
                <textarea value={texto} maxLength={1000} rows={3} onChange={(e) => setTexto(e.target.value)} className={campo} />
              </label>
            ) : null}
            {lote === "encerrar_perdido" ? (
              <label className="text-sm font-semibold">
                Motivo da perda (opcional)
                <select value={motivo} onChange={(e) => setMotivo(e.target.value as MotivoPerda | "")} className={campo}>
                  <option value="">Não informar</option>
                  {MOTIVOS.map((m) => (
                    <option key={m} value={m}>
                      {ROTULO_MOTIVO[m]}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}
            <div className="text-sm">
              <p className="font-semibold">Vai valer para {plural(quantidade, "lead", "leads")}. Exemplos:</p>
              <ul className="mt-1 list-disc pl-5 text-texto-2">
                {exemplos.map((d) => (
                  <li key={d.id}>{d.nome}</li>
                ))}
              </ul>
              <p className="mt-2 text-xs text-texto-2">
                Os leads em que a ação não se aplica são pulados e contados. Dá para desfazer o lote pelo aviso que aparece em seguida.
              </p>
            </div>
            <ErroFormulario texto={erro} />
            <div className="flex justify-end gap-2">
              <button onClick={fecharLote} className={botaoNeutro}>
                Cancelar
              </button>
              <button onClick={aplicar} disabled={enviando} className={botaoPrincipal}>
                {enviando ? "Aplicando…" : `${ROTULO_LOTE[lote]} em ${quantidade.toLocaleString("pt-BR")}`}
              </button>
            </div>
          </div>
        </Dialogo>
      ) : null}
    </div>
  );
}
