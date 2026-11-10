import { Suspense } from "react"

import { PageHeader } from "@/components/shared/page-header"
import { PlaceholderView } from "@/components/shared/placeholder-view"
import { ViewToggle, ViewToggleFallback } from "@/components/shared/view-toggle"
import { PAINEL_VIEWS, readView } from "@/lib/views"

export default function PainelPage({ searchParams }: PageProps<"/">) {
  return (
    <>
      <PageHeader eyebrow="Painel" title="Onde a operação perde tempo e quanto isso custa">
        <Suspense fallback={<ViewToggleFallback options={[...PAINEL_VIEWS]} />}>
          <ViewToggle param="visao" options={[...PAINEL_VIEWS]} defaultValue="diagnostico" label="Visão do painel" />
        </Suspense>
      </PageHeader>
      <Suspense fallback={null}>
        <PainelView searchParams={searchParams} />
      </Suspense>
    </>
  )
}

async function PainelView({ searchParams }: { searchParams: PageProps<"/">["searchParams"] }) {
  const view = readView((await searchParams).visao, PAINEL_VIEWS)
  if (view === "roi")
    return <PlaceholderView owner="Frente A" title="ROI" items={["4 premissas editáveis com origem", "Frase de economia nos casos com autonomia da IA", "Horas, agentes e custo por ticket", "Fórmula legível"]} />
  if (view === "operacao")
    return <PlaceholderView owner="Frente A" title="Operação" items={["% com autonomia (protagonista)", "Distribuição pelos 3 caminhos", "Acurácia ao vivo no holdout", "Revisão humana, latência, custo, base de conhecimento"]} />
  return <PlaceholderView owner="Frente A" title="Diagnóstico" items={["33,3% sem 1ª resposta (protagonista)", "Barras com seletor de métrica e dimensão + selo de significância", "Forest plot do CSAT + callout de sobrevivência"]} />
}
