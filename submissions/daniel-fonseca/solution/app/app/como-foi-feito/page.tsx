import type { Metadata } from "next"
import { Suspense } from "react"

import { PageHeader } from "@/components/shared/page-header"
import { PlaceholderView } from "@/components/shared/placeholder-view"
import { ViewToggle, ViewToggleFallback } from "@/components/shared/view-toggle"
import { METODO_VIEWS, readView } from "@/lib/views"

export const metadata: Metadata = { title: "Como foi feito" }

export default function MetodoPage({ searchParams }: PageProps<"/como-foi-feito">) {
  return (
    <>
      <PageHeader eyebrow="Como foi feito" title="Proposta, decisões e condução do projeto">
        <Suspense fallback={<ViewToggleFallback options={[...METODO_VIEWS]} />}>
          <ViewToggle param="secao" options={[...METODO_VIEWS]} defaultValue="proposta" label="Seção" />
        </Suspense>
      </PageHeader>
      <Suspense fallback={null}>
        <MetodoView searchParams={searchParams} />
      </Suspense>
    </>
  )
}

async function MetodoView({ searchParams }: { searchParams: PageProps<"/como-foi-feito">["searchParams"] }) {
  const view = readView((await searchParams).secao, METODO_VIEWS)
  if (view === "decisoes") return <PlaceholderView owner="Frente A" title="Decisões" items={["Linha do tempo das ADRs", "Destaques do judgment log"]} />
  if (view === "conducao") return <PlaceholderView owner="Frente A" title="Condução" items={["Estrutura do projeto no Claude Code", "Plano e timebox", "Riscos tratados", "Custo do projeto e capacidade"]} />
  return <PlaceholderView owner="Frente A" title="Proposta" items={["Fluxo interativo", "Os 3 caminhos", "O que não automatizar (tickets reais)", "Comparação de métodos e matriz de confusão"]} />
}
