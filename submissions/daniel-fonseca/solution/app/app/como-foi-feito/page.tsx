import type { Metadata } from "next"
import { Suspense } from "react"

import { ConducaoView } from "@/components/metodo/conducao-view"
import { DecisoesView } from "@/components/metodo/decisoes-view"
import { PropostaView } from "@/components/metodo/proposta-view"
import { ViewSkeleton } from "@/components/painel/view-skeleton"
import { PageHeader } from "@/components/shared/page-header"
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
      <Suspense fallback={<ViewSkeleton />}>
        <MetodoView searchParams={searchParams} />
      </Suspense>
    </>
  )
}

async function MetodoView({ searchParams }: { searchParams: PageProps<"/como-foi-feito">["searchParams"] }) {
  const view = readView((await searchParams).secao, METODO_VIEWS)
  if (view === "decisoes") return <DecisoesView />
  if (view === "conducao") return <ConducaoView />
  return <PropostaView />
}
