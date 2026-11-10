import { Suspense } from "react"

import { DiagnosticoView } from "@/components/painel/diagnostico-view"
import { OperacaoView } from "@/components/painel/operacao-view"
import { RoiView } from "@/components/painel/roi-view"
import { ViewSkeleton } from "@/components/painel/view-skeleton"
import { PageHeader } from "@/components/shared/page-header"
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
      <Suspense fallback={<ViewSkeleton />}>
        <PainelView searchParams={searchParams} />
      </Suspense>
    </>
  )
}

async function PainelView({ searchParams }: { searchParams: PageProps<"/">["searchParams"] }) {
  const view = readView((await searchParams).visao, PAINEL_VIEWS)
  if (view === "roi") return <RoiView />
  if (view === "operacao") return <OperacaoView />
  return <DiagnosticoView />
}
