import Link from "next/link";
import type { ReactNode } from "react";
import { FiltrosEquipe } from "@/components/FiltrosEquipe";
import { Funil } from "@/components/Funil";
import { Prioridades } from "@/components/Prioridades";
import { dataBR, dinheiro, dinheiroCurto, inteiro, variacao } from "@/lib/calculos";
import { CONFIG } from "@/lib/config";
import { codificar, type Etiqueta } from "@/lib/filtro/etiquetas";
import { lerFiltrosEquipe } from "@/server/parametros";
import { escopoDe, painel, porVendedor, prioridadesDoDia, somenteLeitura } from "@/server/repositorio";
import { exigirUsuario } from "@/server/sessao";

export const metadata = { title: "Painel" };

function Cartao({ rotulo, valor, linha, selo, sobe, info, href }: { rotulo: string; valor: string; linha?: string; selo?: string | null; sobe?: boolean; info?: string; href?: string }) {
  const corpo: ReactNode = (
    <>
      <p className="text-xs font-semibold text-texto-2">{rotulo}</p>
      <p className="mt-1 font-titulo text-2xl font-bold break-words">{valor}</p>
      {linha ? <p className="mt-1 text-sm text-texto-2">{linha}</p> : null}
      {selo !== undefined ? (
        <p className={`mt-2 inline-block rounded-selo px-2 py-1 text-xs font-semibold ${selo === null ? "bg-trilho text-texto-2" : sobe ? "bg-marinho text-branco" : "bg-aviso-fundo text-bronze-escuro"}`}>
          {selo ?? "sem base para comparar"}
          {selo ? ` vs ${CONFIG.janelaPainelDias} dias antes` : ""}
        </p>
      ) : null}
    </>
  );
  return (
    <div className="rounded-cartao border border-linha bg-fundo p-4 shadow-cartao">
      {href ? (
        <Link href={href} className="block hover:underline">
          {corpo}
        </Link>
      ) : (
        corpo
      )}
      {info ? (
        <details className="mt-2 text-xs text-texto-2">
          <summary className="cursor-pointer font-semibold text-bronze-escuro">Como ler este número</summary>
          <p className="mt-1">{info}</p>
        </details>
      ) : null}
    </div>
  );
}

const filtro = (e: Etiqueta) => `/pipeline?f=${encodeURIComponent(codificar([e]))}`;

export default async function Pagina({ searchParams }: { searchParams: Promise<{ regiao?: string; manager?: string; vendedor?: string }> }) {
  const p = await searchParams;
  const usuario = await exigirUsuario("/painel");
  const filtros = await lerFiltrosEquipe(usuario, p);
  const escopo = escopoDe(usuario, filtros);
  const [{ numeros: n, funil }, prioridades, time] = await Promise.all([
    painel(escopo),
    prioridadesDoDia(usuario),
    usuario.papel === "vendedor" ? Promise.resolve([]) : porVendedor(escopo),
  ]);
  const vLeads = variacao(n.leadsJanela, n.leadsJanelaAnterior);
  const vFech = variacao(n.fechamentosJanela, n.fechamentosJanelaAnterior);
  const vRec = variacao(n.receitaJanela, n.receitaJanelaAnterior);
  const pp = n.conversaoJanela !== null && n.conversaoJanelaAnterior !== null ? Math.round((n.conversaoJanela - n.conversaoJanelaAnterior) * 1000) / 10 : null;
  const trimestre = n.fimDeTrimestre
    ? "Este mês fecha o trimestre. No histórico, os ganhos se concentram no último mês de cada trimestre; compare com o mesmo mês de outro trimestre."
    : undefined;
  const j = CONFIG.janelaPainelDias;

  return (
    <div className="grid gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Painel</h1>
          <p className="text-sm text-texto-2">Dados até {dataBR(n.data)}, em dólares.</p>
        </div>
        <FiltrosEquipe filtros={filtros} />
      </div>

      <div className="grid gap-5 lg:grid-cols-[1fr_22rem]">
        <div className="order-2 grid content-start gap-5 lg:order-1">
          <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <Cartao rotulo="Leads novos" valor={`${inteiro(n.leadsHoje)} hoje`} linha={`${inteiro(n.leadsJanela)} em ${j} dias`} selo={vLeads?.texto ?? null} sobe={vLeads?.sobe} />
            <Cartao rotulo="Em negociação" valor={inteiro(n.emNegociacao)} linha={dinheiroCurto(n.emNegociacaoValor)} href={filtro({ chave: "estagios", valor: ["Engaging"], rotulo: "Estágio: Em negociação" })} />
            <Cartao
              rotulo="Fechamentos"
              valor={`${inteiro(n.fechamentosHoje)} hoje`}
              linha={`${inteiro(n.fechamentosJanela)} em ${j} dias · ${dinheiro(n.fechamentosHojeValor)} hoje`}
              selo={vFech?.texto ?? null}
              sobe={vFech?.sobe}
              info={trimestre}
            />
            <Cartao
              rotulo={`Conversão em ${j} dias`}
              valor={n.conversaoJanela === null ? "—" : `${(n.conversaoJanela * 100).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`}
              linha={`${inteiro(n.fechamentosJanela)} ganhos e ${inteiro(n.perdidosJanela)} perdidos`}
              selo={pp === null ? null : `${pp >= 0 ? "↑" : "↓"} ${Math.abs(pp).toLocaleString("pt-BR")} p.p.`}
              sobe={(pp ?? 0) >= 0}
              info={trimestre}
            />
            <Cartao rotulo={`Receita ganha em ${j} dias`} valor={dinheiroCurto(n.receitaJanela)} selo={vRec?.texto ?? null} sobe={vRec?.sobe} />
            <Cartao rotulo="Pipeline aberto" valor={dinheiroCurto(n.pipelineAbertoValor)} linha={n.pipelinePeloPrecoDeTabela ? "pelo preço de tabela" : "valor esperado"} href="/pipeline" />
            <Cartao rotulo="Total de leads" valor={inteiro(n.totalLeads)} linha="abertos e fechados" />
            <Cartao
              rotulo="Em risco de esfriar"
              valor={inteiro(n.emRisco)}
              linha={`${inteiro(n.esfriou)} já esfriaram`}
              href={filtro({ chave: "icones", valor: ["em_risco"], rotulo: "Ícone: em risco de esfriar" })}
            />
          </div>

          <Funil barras={funil} />

          {time.length ? (
            <section aria-labelledby="t-time" className="rounded-cartao border border-linha bg-fundo p-4 shadow-cartao">
              <h2 id="t-time" className="text-lg font-bold">
                Por vendedor
              </h2>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b-2 border-marinho text-left text-xs text-texto-2">
                      <th className="py-2 pr-3 font-semibold">Vendedor</th>
                      <th className="px-3 py-2 text-right font-semibold">Abertos</th>
                      <th className="px-3 py-2 text-right font-semibold">Em risco</th>
                      <th className="px-3 py-2 text-right font-semibold">Esfriaram</th>
                      <th className="px-3 py-2 text-right font-semibold">Prioridades feitas hoje</th>
                      <th className="py-2 pl-3 text-right font-semibold">Perdidos por falta de atendimento</th>
                    </tr>
                  </thead>
                  <tbody>
                    {time.map((v) => (
                      <tr key={v.vendedor} className="border-b border-linha">
                        <td className="py-2 pr-3">
                          <Link href={`/pipeline?vendedor=${encodeURIComponent(v.vendedor)}`} className="font-semibold hover:underline">
                            {v.vendedor}
                          </Link>
                        </td>
                        <td className="px-3 py-2 text-right">{inteiro(v.abertos)}</td>
                        <td className="px-3 py-2 text-right">{inteiro(v.emRisco)}</td>
                        <td className="px-3 py-2 text-right">{inteiro(v.esfriaram)}</td>
                        <td className="px-3 py-2 text-right">{inteiro(v.prioridadesFeitas)}</td>
                        <td className="py-2 pl-3 text-right">{inteiro(v.perdidosPorFaltaDeAtendimento)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          ) : null}
        </div>

        <div className="order-1 lg:order-2">
          <div className="lg:sticky lg:top-4">
            <Prioridades itens={prioridades} papel={usuario.papel} somenteLeitura={somenteLeitura()} />
          </div>
        </div>
      </div>
    </div>
  );
}
