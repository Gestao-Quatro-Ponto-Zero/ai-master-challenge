import type { Metadata } from "next"
import { Suspense } from "react"

import { DiagnosticoView } from "@/components/painel/diagnostico-view"
import { ViewSkeleton } from "@/components/painel/view-skeleton"

export const metadata: Metadata = { title: "Diagnóstico" }

export default function Page() {
  return (
    <Suspense fallback={<ViewSkeleton />}>
      <DiagnosticoView />
    </Suspense>
  )
}
