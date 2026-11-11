import type { Metadata } from "next"
import { Suspense } from "react"

import { ConducaoView } from "@/components/metodo/conducao-view"
import { ViewSkeleton } from "@/components/painel/view-skeleton"
import { AtRequest } from "@/components/shared/at-request"
import { PageHeader } from "@/components/shared/page-header"

export const metadata: Metadata = { title: "Condução · Como foi feito" }

export default function Page() {
  return (
    <>
      <PageHeader eyebrow="Como foi feito" title="A condução do projeto com IA" />
      <Suspense fallback={<ViewSkeleton />}>
        <AtRequest>
          <ConducaoView />
        </AtRequest>
      </Suspense>
    </>
  )
}
