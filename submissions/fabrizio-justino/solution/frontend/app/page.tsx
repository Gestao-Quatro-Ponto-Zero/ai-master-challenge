"use client"

import { useEffect, useState } from "react"
import { Loader2 } from "lucide-react"
import { Header } from "@/components/header"
import { Filtros } from "@/components/filtros"
import { SeletorData } from "@/components/seletor-data"
import { PainelEmergencia } from "@/components/painel-emergencia"
import { ResumoAcoes } from "@/components/resumo-acoes"
import { AlertaItem } from "@/components/alerta-item"
import { TabelaDeals } from "@/components/tabela-deals"
import { DetalheDeal } from "@/components/detalhe-deal"
import { FilaAlertas } from "@/components/fila-alertas"
import { AbaTime } from "@/components/aba-time"
import { AbaCrossSell } from "@/components/aba-cross-sell"
import { ComoFunciona } from "@/components/como-funciona"
import { CardBriefing } from "@/components/card-briefing"
import { AbaPerguntar } from "@/components/aba-perguntar"
import { AbaEmails } from "@/components/aba-emails"
import { Card } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  api, type AlertasResponse, type BenchmarksResponse, type CrossSellResponse, type DatasResponse, type Deal,
  type EmergenciaResponse, type FiltrosResponse, type PipelineResponse, type Recorte, type TimeResponse,
} from "@/lib/api"
import { dataBr, usd } from "@/lib/format"

interface Painel {
  pipeline: PipelineResponse
  alertas: AlertasResponse
  emergencia: EmergenciaResponse
  time: TimeResponse
  crossSell: CrossSellResponse
}

export default function Home() {
  const [datas, setDatas] = useState<DatasResponse | null>(null)
  const [data, setData] = useState<string>("")
  const [opcoes, setOpcoes] = useState<FiltrosResponse | null>(null)
  const [benchmarks, setBenchmarks] = useState<BenchmarksResponse | null>(null)
  const [recorte, setRecorte] = useState<Recorte>({})
  const [painel, setPainel] = useState<Painel | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const [dealAberto, setDealAberto] = useState<Deal | null>(null)

  useEffect(() => {
    api.datas().then((d) => { setDatas(d); setData(d.padrao) }).catch((e) => setErro(e.message))
  }, [])

  // Opções de filtro e benchmarks mudam com a data (snapshot diferente)
  useEffect(() => {
    if (!data) return
    Promise.all([api.filtros(data), api.benchmarks(data)])
      .then(([f, b]) => { setOpcoes(f); setBenchmarks(b) })
      .catch((e) => setErro(e.message))
  }, [data])

  useEffect(() => {
    if (!data) return
    setCarregando(true)
    setErro("")
    Promise.all([api.pipeline(data, recorte), api.alertas(data, recorte), api.emergencia(data, recorte), api.time(data, recorte), api.crossSell(data, recorte)])
      .then(([pipeline, alertas, emergencia, time, crossSell]) => setPainel({ pipeline, alertas, emergencia, time, crossSell }))
      .catch((e) => setErro(e.message))
      .finally(() => setCarregando(false))
  }, [data, recorte])

  // Alertas e lista de resgate apontam pro deal pelo id
  const abrirDealPorId = (id: string) => {
    const d = painel?.pipeline.deals.find((x) => x.opportunity_id === id)
    if (d) setDealAberto(d)
  }

  const chave = `${data}-${JSON.stringify(recorte)}`

  return (
    <div className="app-bg min-h-screen">
      <Header dataReferencia={data || undefined} />
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6 md:px-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end">
          {datas && <SeletorData datas={datas} valor={data} onChange={(d) => { setData(d); setRecorte({}) }} />}
          {opcoes && <div className="flex-1"><Filtros opcoes={opcoes} recorte={recorte} onChange={setRecorte} /></div>}
        </div>

        {erro && <Card className="border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">{erro}</Card>}

        {carregando && !painel ? (
          <div className="flex items-center justify-center gap-2 py-20 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" /> Calculando o pipeline...
          </div>
        ) : painel ? (
          <>
            <CardBriefing data={data} recorte={recorte} />

            <PainelEmergencia e={painel.emergencia} data={data} recorte={recorte} onAbrirDeal={abrirDealPorId} />

            {painel.alertas.time.filter((a) => a.tipo !== "emergencia").length > 0 && (
              <section className="grid gap-2 md:grid-cols-2">
                {painel.alertas.time.filter((a) => a.tipo !== "emergencia").map((a) => <AlertaItem key={a.tipo + a.titulo} alerta={a} />)}
              </section>
            )}

            <section className="space-y-2">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <h2 className="text-sm font-bold uppercase tracking-widest text-primary/80">Seu pipeline</h2>
                <span className="text-xs text-muted-foreground">
                  {painel.pipeline.resumo.total} deals abertos · {usd(painel.pipeline.resumo.valor_esperado_total)} esperado até{" "}
                  {dataBr(painel.pipeline.horizonte.fim)}
                  {carregando && <Loader2 className="ml-2 inline h-3 w-3 animate-spin" />}
                </span>
              </div>
              <ResumoAcoes
                resumo={painel.pipeline.resumo}
                acaoAtiva={recorte.acao}
                onSelecionar={(acao) => setRecorte({ ...recorte, acao })}
              />
            </section>

            <Tabs defaultValue="prioridades">
              <TabsList className="flex-wrap">
                <TabsTrigger value="prioridades">Prioridades</TabsTrigger>
                <TabsTrigger value="alertas">
                  Alertas ({painel.alertas.contagem.critico} críticos)
                </TabsTrigger>
                <TabsTrigger value="perguntar">Perguntar</TabsTrigger>
                <TabsTrigger value="time">Time</TabsTrigger>
                <TabsTrigger value="cross-sell">Cross-sell ({painel.crossSell.total})</TabsTrigger>
                <TabsTrigger value="emails">E-mails</TabsTrigger>
                <TabsTrigger value="como-funciona">Como o score funciona</TabsTrigger>
              </TabsList>
              <TabsContent value="prioridades" className="mt-4">
                <TabelaDeals key={chave} deals={painel.pipeline.deals} onAbrir={setDealAberto} />
              </TabsContent>
              <TabsContent value="alertas" className="mt-4">
                <FilaAlertas key={chave} dados={painel.alertas} onAbrirDeal={abrirDealPorId} />
              </TabsContent>
              <TabsContent value="perguntar" className="mt-4">
                <AbaPerguntar key={data} data={data} onAbrirDeal={abrirDealPorId} />
              </TabsContent>
              <TabsContent value="time" className="mt-4">
                <AbaTime t={painel.time} data={data} recorte={recorte} />
              </TabsContent>
              <TabsContent value="cross-sell" className="mt-4">
                <AbaCrossSell cs={painel.crossSell} />
              </TabsContent>
              <TabsContent value="emails" className="mt-4">
                <AbaEmails data={data} />
              </TabsContent>
              <TabsContent value="como-funciona" className="mt-4">
                {benchmarks && <ComoFunciona bm={benchmarks} />}
              </TabsContent>
            </Tabs>
          </>
        ) : null}
      </main>
      <DetalheDeal deal={dealAberto} data={data} onFechar={() => setDealAberto(null)} />
    </div>
  )
}
