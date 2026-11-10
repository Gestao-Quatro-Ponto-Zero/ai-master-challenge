import type { Metadata } from "next"
import { Suspense } from "react"

import { OperacaoView } from "@/components/painel/operacao-view"
import { ViewSkeleton } from "@/components/painel/view-skeleton"

export const metadata: Metadata = { title: "Operação" }

export default function Page() {
  return (
    <Suspense fallback={<ViewSkeleton />}>
      <OperacaoView />
    </Suspense>
  )
}
