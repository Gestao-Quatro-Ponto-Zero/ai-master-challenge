import type { Metadata } from "next"
import { Suspense } from "react"

import { DecisoesView } from "@/components/metodo/decisoes-view"
import { ViewSkeleton } from "@/components/painel/view-skeleton"
import { PageHeader } from "@/components/shared/page-header"

export const metadata: Metadata = { title: "Decisões · Como foi feito" }

export default function Page() {
  return (
    <>
      <PageHeader eyebrow="Como foi feito" title="As decisões do projeto" />
      <Suspense fallback={<ViewSkeleton />}>
        <DecisoesView />
      </Suspense>
    </>
  )
}
