import Link from "next/link";
import { FiltrosEquipe } from "@/components/FiltrosEquipe";
import { Funil } from "@/components/Funil";
import { Prioridades } from "@/components/Prioridades";
import { CartaoNumero, PilulaVariacao } from "@/components/ui/CartaoNumero";
import { Etiqueta as EtiquetaUi } from "@/components/ui/Etiqueta";
import { classeSuperficie } from "@/components/ui/Superficie";
import { dataBR, dinheiro, dinheiroCurto, inteiro, NOME_MOEDA, variacao } from "@/lib/calculos";
import { CONFIG } from "@/lib/config";
import { codificar, type Etiqueta } from "@/lib/filtro/etiquetas";
import { lerFiltrosEquipe } from "@/server/parametros";
import { escopoDe, painel, porVendedor, prioridadesDoDia, somenteLeitura } from "@/server/repositorio";
import { exigirUsuario } from "@/server/sessao";

export const metadata = { title: "Painel" };

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
  // Como no modelo: "18% vs 30d ant."
  const vs = (v: { texto: string; sobe: boolean } | null) => (v ? { texto: `${v.texto} vs ${j}d ant.`, sobe: v.sobe } : null);

  return (
    <div className="grid grid-cols-1 gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Painel</h1>
          <p className="text-sm text-texto-2">Dados até {dataBR(n.data)}, em {NOME_MOEDA}.</p>
        </div>
        <FiltrosEquipe filtros={filtros} />
      </div>

      {/* Grade responsiva (O-32):
          ≥ 1280: a grade 4 × 4 do modelo (Prioridades e funil no meio);
          1024–1279: Prioridades e funil em largura cheia no topo e os 8 números em 4 colunas embaixo;
          < 1024: Prioridades, números em 2 colunas e funil. */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4 xl:auto-rows-[minmax(9.5rem,auto)]">
        <Prioridades
          itens={prioridades}
          papel={usuario.papel}
          somenteLeitura={somenteLeitura()}
          className="order-1 col-span-2 lg:col-span-4 xl:order-none xl:col-span-2 xl:col-start-2 xl:row-span-2 xl:row-start-1 xl:h-0 xl:min-h-full"
          topo={
            <Link href={filtro({ chave: "icones", valor: ["em_risco"], rotulo: "Ícone: em risco de esfriar" })} className="rounded-selo hover:opacity-80" title="Ver os deals em risco de esfriar no Pipeline">
              <EtiquetaUi tom="atencao" icone="alerta">
                {inteiro(n.emRisco)} em risco · {inteiro(n.esfriou)} já esfriaram
              </EtiquetaUi>
            </Link>
          }
        />

        <CartaoNumero
          grupo="negociacao"
          icone="cifrao"
          rotulo="Pipeline aberto"
          valor={dinheiroCurto(n.pipelineAbertoValor)}
          linha={n.pipelinePeloPrecoDeTabela ? "pelo preço de tabela" : "valor esperado"}
          href="/pipeline"
          className="order-2 lg:order-3 xl:order-none xl:col-start-1 xl:row-start-1"
        />
        <CartaoNumero
          grupo="negociacao"
          icone="conversa"
          rotulo="Em negociação"
          valor={inteiro(n.emNegociacao)}
          linha={dinheiroCurto(n.emNegociacaoValor)}
          href={filtro({ chave: "estagios", valor: ["Engaging"], rotulo: "Estágio: Em negociação" })}
          className="order-2 lg:order-3 xl:order-none xl:col-start-4 xl:row-start-1"
        />
        <CartaoNumero grupo="leads" icone="pessoa-mais" rotulo="Leads hoje" valor={inteiro(n.leadsHoje)} className="order-2 lg:order-3 xl:order-none xl:col-start-1 xl:row-start-2" />
        <CartaoNumero
          grupo="fechamento"
          icone="check"
          rotulo="Fechamentos hoje"
          valor={inteiro(n.fechamentosHoje)}
          linha={`${dinheiro(n.fechamentosHojeValor)} hoje`}
          className="order-2 lg:order-3 xl:order-none xl:col-start-4 xl:row-start-2"
        />
        <CartaoNumero
          grupo="leads"
          icone="calendario"
          rotulo={`Leads em ${j} dias`}
          valor={inteiro(n.leadsJanela)}
          rodape={<PilulaVariacao variacao={vs(vLeads)} />}
          className="order-2 lg:order-3 xl:order-none xl:col-start-1 xl:row-start-3"
        />
        <CartaoNumero
          grupo="fechamento"
          icone="trofeu"
          rotulo={`Fechamentos em ${j} dias`}
          valor={inteiro(n.fechamentosJanela)}
          linha={`${dinheiroCurto(n.receitaJanela)} em receita ganha`}
          rodape={
            <>
              <PilulaVariacao variacao={vs(vFech)} />
              <PilulaVariacao variacao={vRec} rotulo="receita" />
            </>
          }
          info={trimestre}
          className="order-2 lg:order-3 xl:order-none xl:col-start-4 xl:row-start-3"
        />
        <CartaoNumero
          destaque
          grupo="leads"
          icone="pessoas"
          rotulo="Total de leads"
          valor={inteiro(n.totalLeads)}
          linha="abertos e fechados"
          className="order-2 lg:order-3 xl:order-none xl:col-start-1 xl:row-start-4"
        />
        <CartaoNumero
          grupo="fechamento"
          icone="percentual"
          rotulo={`Conversão em ${j} dias`}
          valor={n.conversaoJanela === null ? "—" : `${(n.conversaoJanela * 100).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`}
          linha={`${inteiro(n.fechamentosJanela)} fechados e ${inteiro(n.perdidosJanela)} perdidos`}
          rodape={<PilulaVariacao variacao={pp === null ? null : { texto: `${Math.abs(pp).toLocaleString("pt-BR")} p.p. vs ${j}d ant.`, sobe: pp >= 0 }} />}
          info={trimestre}
          className="order-2 lg:order-3 xl:order-none xl:col-start-4 xl:row-start-4"
        />

        <Funil barras={funil} className="order-3 col-span-2 lg:order-2 lg:col-span-4 xl:order-none xl:col-span-2 xl:col-start-2 xl:row-span-2 xl:row-start-3" />
      </div>

          {time.length ? (
            <section aria-labelledby="t-time" className={`${classeSuperficie} p-4`}>
              <h2 id="t-time" className="text-lg font-bold">
                Por vendedor
              </h2>
              <div className="mt-3 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-borda text-left text-xs text-texto-2">
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
                      <tr key={v.vendedor} className="h-11 border-b border-divisoria last:border-0">
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
  );
}
