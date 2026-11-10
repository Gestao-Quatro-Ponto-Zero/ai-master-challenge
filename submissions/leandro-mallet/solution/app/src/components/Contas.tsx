"use client";
// Aba Contas: lista das empresas, ficha (cadastro, histórico, padrão de compra, deals abertos) e cadastro.
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { pedir } from "@/lib/cliente";
import { dataBR, dinheiro, dinheiroCurto, inteiro, ROTULO_ESTAGIO, ROTULO_PORTE, rotuloSetor, SETORES } from "@/lib/calculos";
import type { ContaDetalhe, ContaVisao } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { botaoNeutro, botaoPrincipal, botaoSecundario, campo, Dialogo, ErroFormulario } from "./Dialogo";
import { Esqueleto, Estado } from "./Estado";
import { BarraNota, IconeDeal } from "./Nota";

const PADRAO: Record<NonNullable<ContaVisao["padrao"]>, { rotulo: string; classe: string }> = {
  na_janela: { rotulo: "Na janela de compra", classe: "bg-dourado text-marinho" },
  fora_da_janela: { rotulo: "Fora da janela", classe: "border border-linha-forte text-texto" },
  sem_padrao: { rotulo: "Sem padrão", classe: "bg-trilho text-texto-2" },
};

function SeloPadrao({ c }: { c: ContaVisao }) {
  if (!c.padrao) return <span className="rounded-selo bg-trilho px-2 py-1 text-xs whitespace-nowrap text-texto-2">Calculado no domingo</span>;
  const p = PADRAO[c.padrao];
  return (
    <span className={`rounded-selo px-2 py-1 text-xs font-semibold whitespace-nowrap ${p.classe}`}>
      {p.rotulo}
      {c.bonus !== null ? ` · bônus ${c.bonus}` : ""}
    </span>
  );
}

export function TabelaContas({ contas, empresas, podeEditar }: { contas: ContaVisao[]; empresas: string[]; podeEditar: boolean }) {
  const somenteLeitura = !podeEditar;
  const params = useSearchParams();
  const caminho = usePathname();
  const router = useRouter();
  const aberta = params.get("conta");
  const [nova, setNova] = useState(false);
  const link = (nome: string) => {
    const p = new URLSearchParams(params.toString());
    p.set("conta", nome);
    return `${caminho}?${p}`;
  };
  const fechar = useCallback(() => {
    const p = new URLSearchParams(params.toString());
    p.delete("conta");
    router.replace(`${caminho}?${p}`, { scroll: false });
  }, [params, caminho, router]);
  const fecharNova = useCallback(() => setNova(false), []);

  return (
    <div className="grid gap-3">
      {somenteLeitura ? null : (
        <div className="flex justify-end">
          <button onClick={() => setNova(true)} className={botaoPrincipal}>
            Nova empresa
          </button>
        </div>
      )}
      {contas.length === 0 ? (
        <Estado titulo="Nenhuma empresa com estes filtros" texto="Remova uma etiqueta acima ou limpe os filtros para ver todas as empresas." />
      ) : (
        <div className="overflow-x-auto rounded-cartao border border-linha bg-fundo shadow-cartao">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b-2 border-marinho bg-marfim text-left text-xs text-texto-2">
                <th className="px-3 py-2 font-semibold">Empresa</th>
                <th className="px-3 py-2 font-semibold">Setor</th>
                <th className="px-3 py-2 font-semibold">Porte</th>
                <th className="px-3 py-2 font-semibold">Sede</th>
                <th className="px-3 py-2 text-right font-semibold">Deals abertos</th>
                <th className="px-3 py-2 text-right font-semibold">Compras</th>
                <th className="px-3 py-2 text-right font-semibold">Receita ganha</th>
                <th className="px-3 py-2 font-semibold">Padrão de compra</th>
              </tr>
            </thead>
            <tbody>
              {contas.map((c) => (
                <tr key={c.nome} className="border-b border-linha align-top">
                  <td className="px-3 py-2">
                    <Link href={link(c.nome)} scroll={false} className="font-semibold hover:underline">
                      {c.nome}
                    </Link>
                    {c.empresaMae ? <span className="block text-xs text-texto-2">do grupo {c.empresaMae}</span> : null}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap">{rotuloSetor(c.setor)}</td>
                  <td className="px-3 py-2">{c.porte ? ROTULO_PORTE[c.porte] : "—"}</td>
                  <td className="px-3 py-2 whitespace-nowrap">{c.sede ?? "—"}</td>
                  <td className="px-3 py-2 text-right">{inteiro(c.dealsAbertos)}</td>
                  <td className="px-3 py-2 text-right">{inteiro(c.compras)}</td>
                  <td className="px-3 py-2 text-right whitespace-nowrap">{dinheiro(c.receitaGanha)}</td>
                  <td className="px-3 py-2">
                    <SeloPadrao c={c} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {aberta ? <FichaConta key={aberta} nome={aberta} empresas={empresas} somenteLeitura={somenteLeitura} onFechar={fechar} /> : null}
      {nova ? (
        <Dialogo titulo="Nova empresa" onFechar={fecharNova}>
          <FormularioConta empresas={empresas} onPronto={fecharNova} />
        </Dialogo>
      ) : null}
    </div>
  );
}

function FichaConta({ nome, empresas, somenteLeitura, onFechar }: { nome: string; empresas: string[]; somenteLeitura: boolean; onFechar: () => void }) {
  const avisos = useAvisos();
  const params = useSearchParams();
  const caminho = usePathname();
  const [det, setDet] = useState<ContaDetalhe | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [tentativa, setTentativa] = useState(0);
  const [editando, setEditando] = useState(false);

  useEffect(() => {
    let vivo = true;
    (async () => {
      const r = await pedir<ContaDetalhe>(`/api/contas/${encodeURIComponent(nome)}`);
      if (!vivo) return;
      if (r.ok && r.dados) {
        setDet(r.dados);
        setErro(null);
      } else setErro(r.erro ?? "Não foi possível abrir esta empresa.");
    })();
    return () => {
      vivo = false;
    };
  }, [nome, tentativa, avisos.revisao]);

  const linkDeal = (id: string) => {
    const p = new URLSearchParams(params.toString());
    p.delete("conta");
    p.set("deal", id);
    return `${caminho}?${p}`;
  };
  const c = det?.conta;
  const maxMes = Math.max(1, ...(det?.porMes ?? []).map((m) => m.ganhos + m.perdidos));

  return (
    <Dialogo titulo={nome} largo onFechar={onFechar}>
      {erro ? (
        <Estado erro titulo="Não foi possível abrir esta empresa" texto={erro}>
          <button onClick={() => setTentativa((t) => t + 1)} className={botaoPrincipal}>
            Tentar de novo
          </button>
        </Estado>
      ) : !det || !c ? (
        <div className="grid gap-3" aria-busy="true" aria-label="Carregando a empresa">
          <Esqueleto className="h-5 w-1/2" />
          <Esqueleto className="h-40" />
          <Esqueleto className="h-24" />
        </div>
      ) : editando ? (
        <FormularioConta conta={c} empresas={empresas.filter((e) => e !== c.nome)} onPronto={() => setEditando(false)} />
      ) : (
        <div className="grid gap-6">
          <section aria-label="Cadastro">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <dl className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm sm:grid-cols-3">
                {(
                  [
                    ["Setor", rotuloSetor(c.setor)],
                    ["Porte", c.porte ? ROTULO_PORTE[c.porte] : "—"],
                    ["Funcionários", c.funcionarios !== null ? inteiro(c.funcionarios) : "—"],
                    ["Receita anual", c.receitaMilhoes !== null ? `US$ ${c.receitaMilhoes.toLocaleString("pt-BR")} mi` : "—"],
                    ["Fundação", c.anoFundacao ?? "—"],
                    ["Sede", c.sede ?? "—"],
                    ["Empresa-mãe", c.empresaMae ?? "Independente"],
                  ] as const
                ).map(([rot, v]) => (
                  <div key={rot}>
                    <dt className="text-xs text-texto-2">{rot}</dt>
                    <dd className="font-semibold">{v}</dd>
                  </div>
                ))}
              </dl>
              {somenteLeitura ? null : (
                <button onClick={() => setEditando(true)} className={botaoSecundario}>
                  Editar cadastro
                </button>
              )}
            </div>
          </section>

          <section aria-labelledby="t-historico">
            <h3 id="t-historico" className="text-base font-bold">
              Histórico de compras
            </h3>
            <dl className="mt-2 grid grid-cols-2 gap-2 text-center text-sm sm:grid-cols-4">
              {(
                [
                  ["Compras", inteiro(c.compras)],
                  ["Perdidos", inteiro(c.perdas)],
                  ["Receita ganha", dinheiroCurto(c.receitaGanha)],
                  ["Ticket médio", dinheiro(det.ticketMedio)],
                ] as const
              ).map(([rot, v]) => (
                <div key={rot} className="rounded-controle border border-linha px-2 py-2">
                  <dt className="text-xs text-texto-2">{rot}</dt>
                  <dd className="font-titulo text-lg font-bold">{v}</dd>
                </div>
              ))}
            </dl>
            {det.porMes.length === 0 ? (
              <p className="mt-3 text-sm text-texto-2">Esta empresa ainda não tem deals fechados.</p>
            ) : (
              <>
                <div className="mt-4 flex h-32 items-end gap-1" role="img" aria-label={`Ganhos e perdidos por mês, de ${det.porMes[0]?.mes} a ${det.porMes.at(-1)?.mes}`}>
                  {det.porMes.map((m) => (
                    <div key={m.mes} className="flex h-full min-w-0 flex-1 flex-col justify-end" title={`${m.mes.slice(5)}/${m.mes.slice(0, 4)}: ${m.ganhos} ganhos e ${m.perdidos} perdidos`}>
                      <div className="rounded-t-sm bg-cinza" style={{ height: `${(m.perdidos / maxMes) * 100}%` }} />
                      <div className="bg-marinho" style={{ height: `${(m.ganhos / maxMes) * 100}%` }} />
                      <span className="mt-1 text-center text-xs text-texto-2">{m.mes.slice(5)}</span>
                    </div>
                  ))}
                </div>
                <p className="mt-2 flex flex-wrap gap-4 text-xs text-texto-2">
                  <span className="inline-flex items-center gap-1">
                    <span className="h-2 w-3 bg-marinho" aria-hidden /> ganhos
                  </span>
                  <span className="inline-flex items-center gap-1">
                    <span className="h-2 w-3 bg-cinza" aria-hidden /> perdidos
                  </span>
                  <span>
                    Primeira compra em {dataBR(det.primeiraCompra)}; última em {dataBR(det.ultimaCompra)}.
                  </span>
                </p>
                <table className="mt-3 w-full text-sm">
                  <thead>
                    <tr className="border-b border-linha-forte text-left text-xs text-texto-2">
                      <th className="py-1 font-semibold">Produto comprado</th>
                      <th className="py-1 text-right font-semibold">Compras</th>
                      <th className="py-1 text-right font-semibold">Receita</th>
                    </tr>
                  </thead>
                  <tbody>
                    {det.produtos.map((p) => (
                      <tr key={p.produto} className="border-b border-linha">
                        <td className="py-1">{p.produto}</td>
                        <td className="py-1 text-right">{inteiro(p.compras)}</td>
                        <td className="py-1 text-right">{dinheiro(p.receita)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </>
            )}
          </section>

          <section aria-labelledby="t-padrao" className="rounded-cartao border border-linha-forte bg-marfim p-4">
            <h3 id="t-padrao" className="text-base font-bold">
              Padrão de compra
            </h3>
            {det.padrao ? (
              <>
                <dl className="mt-2 grid grid-cols-2 gap-2 text-sm sm:grid-cols-4">
                  {(
                    [
                      ["Intervalo típico", det.padrao.intervaloTipicoDias !== null ? `${det.padrao.intervaloTipicoDias} dias` : "—"],
                      ["Mês habitual", det.padrao.mesHabitual ?? "—"],
                      ["Próxima compra", dataBR(det.padrao.proximaCompra)],
                      ["Bônus atual", c.bonus ?? "—"],
                    ] as const
                  ).map(([rot, v]) => (
                    <div key={rot}>
                      <dt className="text-xs text-texto-2">{rot}</dt>
                      <dd className="font-semibold">{v}</dd>
                    </div>
                  ))}
                </dl>
                {det.padrao.explicacao ? <p className="mt-2 text-sm">{det.padrao.explicacao}</p> : null}
              </>
            ) : (
              <p className="mt-2 text-sm text-texto-2">
                Calculado no domingo. O padrão mostra o intervalo típico entre compras, o mês habitual e a próxima compra esperada, e define o bônus da empresa na nota (0 a 20).
              </p>
            )}
          </section>

          <section aria-labelledby="t-abertos">
            <h3 id="t-abertos" className="text-base font-bold">
              Deals abertos ({det.abertos.length})
            </h3>
            {det.abertos.length === 0 ? (
              <p className="mt-2 text-sm text-texto-2">Nenhum deal aberto com esta empresa.</p>
            ) : (
              <ul className="mt-2 grid gap-2">
                {det.abertos.map((d) => (
                  <li key={d.id} className="flex flex-wrap items-center gap-3 rounded-controle border border-linha px-3 py-2 text-sm">
                    <Link href={linkDeal(d.id)} scroll={false} className="min-w-0 flex-1 font-semibold break-words hover:underline">
                      {d.nome}
                    </Link>
                    <span className="text-texto-2">
                      {ROTULO_ESTAGIO[d.estagio]} · {d.vendedor}
                    </span>
                    <span className="w-32">
                      <BarraNota score={d.score} faixa={d.faixaNota} />
                    </span>
                    <IconeDeal icone={d.icone} dias={d.diasDesdeAbertura} />
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}
    </Dialogo>
  );
}

function FormularioConta({ conta, empresas, onPronto }: { conta?: ContaVisao; empresas: string[]; onPronto: () => void }) {
  const avisos = useAvisos();
  const [nome, setNome] = useState(conta?.nome ?? "");
  const [setor, setSetor] = useState(conta?.setor ?? "");
  const [funcionarios, setFuncionarios] = useState(conta?.funcionarios?.toString() ?? "");
  const [receita, setReceita] = useState(conta?.receitaMilhoes?.toString() ?? "");
  const [ano, setAno] = useState(conta?.anoFundacao?.toString() ?? "");
  const [sede, setSede] = useState(conta?.sede ?? "");
  const [mae, setMae] = useState(conta?.empresaMae ?? "");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const numero = (t: string) => (t.trim() === "" ? null : Number(t.replace(",", ".")));

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    if (!nome.trim()) return setErro("Informe o nome da empresa.");
    const f = numero(funcionarios);
    const r0 = numero(receita);
    const a = numero(ano);
    if ([f, r0, a].some((v) => v !== null && !Number.isFinite(v))) return setErro("Use só números em funcionários, receita e ano.");
    if (mae && !empresas.includes(mae)) return setErro("A empresa-mãe precisa estar cadastrada.");
    setEnviando(true);
    setErro(null);
    const r = await pedir("/api/contas", "POST", {
      nome: nome.trim(), novo: !conta, setor: setor || null, funcionarios: f === null ? null : Math.round(f), receitaMilhoes: r0, anoFundacao: a === null ? null : Math.round(a), sede: sede || null, empresaMae: mae || null,
    });
    setEnviando(false);
    if (!r.ok) return setErro(r.erro ?? "Não foi possível salvar. Tente de novo.");
    avisos.ok(conta ? "Cadastro da empresa atualizado." : "Empresa cadastrada.");
    avisos.atualizar();
    onPronto();
  }

  return (
    <form onSubmit={salvar} className="grid gap-3 sm:grid-cols-2">
      <label className="text-sm font-semibold sm:col-span-2">
        Nome
        <input value={nome} maxLength={120} disabled={!!conta} onChange={(e) => setNome(e.target.value)} className={`${campo} disabled:bg-trilho`} autoFocus={!conta} />
        {conta ? <span className="mt-1 block text-xs font-normal text-texto-2">O nome não muda depois de criado.</span> : null}
      </label>
      <label className="text-sm font-semibold">
        Setor
        <select value={setor} onChange={(e) => setSetor(e.target.value)} className={campo}>
          <option value="">Não informado</option>
          {Object.entries(SETORES).map(([en, pt]) => (
            <option key={en} value={en}>
              {pt}
            </option>
          ))}
        </select>
      </label>
      <label className="text-sm font-semibold">
        Sede (país)
        <input value={sede} maxLength={80} onChange={(e) => setSede(e.target.value)} className={campo} />
      </label>
      <label className="text-sm font-semibold">
        Funcionários
        <input inputMode="numeric" value={funcionarios} onChange={(e) => setFuncionarios(e.target.value)} className={campo} />
      </label>
      <label className="text-sm font-semibold">
        Receita anual (US$ milhões)
        <input inputMode="decimal" value={receita} onChange={(e) => setReceita(e.target.value)} className={campo} />
      </label>
      <label className="text-sm font-semibold">
        Ano de fundação
        <input inputMode="numeric" value={ano} onChange={(e) => setAno(e.target.value)} className={campo} />
      </label>
      <label className="text-sm font-semibold">
        Empresa-mãe (opcional)
        <input list="lista-maes" value={mae} onChange={(e) => setMae(e.target.value)} placeholder="Digite para buscar" className={campo} />
        <datalist id="lista-maes">
          {empresas.map((c) => (
            <option key={c} value={c} />
          ))}
        </datalist>
      </label>
      <div className="grid gap-3 sm:col-span-2">
        <ErroFormulario texto={erro} />
        <div className="flex justify-end gap-2">
          <button type="button" onClick={onPronto} className={botaoNeutro}>
            Cancelar
          </button>
          <button type="submit" disabled={enviando} className={botaoPrincipal}>
            {enviando ? "Salvando…" : conta ? "Salvar cadastro" : "Cadastrar empresa"}
          </button>
        </div>
      </div>
    </form>
  );
}
