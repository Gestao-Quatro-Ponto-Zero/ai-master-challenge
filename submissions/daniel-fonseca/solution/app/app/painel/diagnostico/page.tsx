import type { Metadata } from "next"
import { Suspense } from "react"

import { DiagnosticoView } from "@/components/painel/diagnostico-view"
import { ViewSkeleton } from "@/components/painel/view-skeleton"
import { AtRequest } from "@/components/shared/at-request"

export const metadata: Metadata = { title: "Diagnóstico" }

export default function Page() {
  return (
    <Suspense fallback={<ViewSkeleton />}>
      <AtRequest>
        <DiagnosticoView />
      </AtRequest>
    </Suspense>
  )
}
