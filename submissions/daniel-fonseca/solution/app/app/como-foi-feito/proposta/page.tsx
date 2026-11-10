import type { Metadata } from "next"
import { Suspense } from "react"

import { PropostaView } from "@/components/metodo/proposta-view"
import { ViewSkeleton } from "@/components/painel/view-skeleton"
import { PageHeader } from "@/components/shared/page-header"

export const metadata: Metadata = { title: "Proposta · Como foi feito" }

export default function Page() {
  return (
    <>
      <PageHeader eyebrow="Como foi feito" title="A proposta de automação" />
      <Suspense fallback={<ViewSkeleton />}>
        <PropostaView />
      </Suspense>
    </>
  )
}
